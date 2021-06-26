import os
from django.db import models
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core.validators import ValidationError
from django.conf import settings
from django.db.models.signals import (
    post_save,
    m2m_changed,
    post_delete,
    pre_save,
    pre_delete,
)


class Server(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False, unique=True)
    address = models.GenericIPAddressField(max_length=32, blank=False, null=True)
    is_active = models.BooleanField(default=True, verbose_name="active")

    class Meta:
        verbose_name = "Servers"
        verbose_name_plural = "Servers"
        ordering = ("-id",)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("server-detail", kwargs={"pk": self.pk})


class ServerGroup(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False, unique=True)
    servers = models.ManyToManyField(Server, related_name="group_servers", null=False)
    is_active = models.BooleanField(default=True, verbose_name="active")

    class Meta:
        ordering = [
            "-id",
        ]

    def get_absolute_url(self):
        return reverse("group-detail", kwargs={"pk": self.pk})

    def clean(self, *args, **kwargs):
        if " " in self.name:  # in ['0.0.0.0', '127.0.0.1']:
            raise ValidationError("Space not allowed in Group name")

        if self.name[0].isdigit():
            raise ValidationError("Group name could not start with digit")

    def __str__(self):
        return self.name


class Upgrade(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    current_version = models.CharField(max_length=255, null=True, blank=True)
    new_version = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name


class UpgradeResult(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    unreachable_count = models.IntegerField(default=0)

    groups = models.TextField(null=True, blank=True)

    fail_msg = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return str(self.name)

    def get_result_detail(self):
        return UpgradeResultDetails.objects.filter(upgrade_result=self)


class UpgradeResultDetails(models.Model):
    package_name = models.CharField(max_length=255, default="")
    package = models.CharField(max_length=255, default="")
    upgrade_result = models.ForeignKey(to=UpgradeResult, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=50)
    pid = models.CharField(max_length=50)
    event = models.CharField(max_length=50)
    host = models.CharField(max_length=50)
    last_version = models.CharField(max_length=250, null=True, blank=True)
    upgraded_version = models.CharField(max_length=250, null=True, blank=True)
    state = models.CharField(max_length=50)
    changed = models.BooleanField(null=True, blank=True)
    msg = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.CharField(max_length=150, null=True, blank=True)
    resp_dump = models.TextField(null=True, blank=True)
    runner_result = models.CharField(max_length=120, default="Unknown")

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return str(self.host)


def save_config_file(sender, instance, *args, **kwargs):
    print("kwargs", kwargs)
    path = settings.ANSIBLE_CONF_PATH
    file = "{}{}".format(path, instance.name)
    servers = instance.servers.all()
    with open(file, "w+") as f:
        f.writelines(["[{}]\n".format(instance.name)])
        for server in servers:
            f.write("{} \n".format(server.address))


m2m_changed.connect(save_config_file, sender=ServerGroup.servers.through)
post_save.connect(save_config_file, sender=ServerGroup)


def server_updated(sender, instance, *args, **kwargs):
    print(instance)
    groups = instance.group_servers.all()
    print("called", groups)
    if groups:
        for group in groups:
            print("group", group)
            m2m_changed.send(
                sender=ServerGroup.servers.through, instance=group, created=False
            )
            # post_delete.send(sender=NodeGroup, instance=group, created=False)


def servers_deleted(sender, instance, *args, **kwargs):
    print(instance)
    groups = instance.group_servers.all()
    print("Yay called", groups)
    if groups:
        for group in groups:

            print("group", group)
            group.servers.remove(instance)


post_save.connect(server_updated, sender=Server)
pre_delete.connect(servers_deleted, sender=Server)


def remove_config_file_group_delete(sender, instance, *args, **kwargs):
    path = settings.ANSIBLE_CONF_PATH
    file = "{}{}".format(path, instance.name)
    if os.path.exists(file):
        os.remove(file)


post_delete.connect(remove_config_file_group_delete, sender=ServerGroup)


def remove_config_file_group_name_updated(sender, instance, *args, **kwargs):
    if instance.id:
        pre_save_instance = ServerGroup.objects.get(id=instance.id)
        if instance.name != pre_save_instance.name:
            path = settings.ANSIBLE_CONF_PATH
            file = "{}{}".format(path, pre_save_instance.name)
            if os.path.exists(file):
                os.remove(file)


pre_save.connect(remove_config_file_group_name_updated, sender=ServerGroup)
