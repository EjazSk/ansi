from os import system
import os
import yaml
import time
from datetime import datetime

from django.conf import settings
from django.utils import timezone

import ansible_runner
from celery import shared_task

from .models import Upgrade, UpgradeResult


def get_patch_data():
    # print('CALLED')
    Upgrade.objects.all().delete()
    filename = "/tmp/" + str(datetime.now()).replace(" ", "")
    # print filename
    patchlist = []
    # system('apt list --upgradable | grep security >> {}'.format(filename))
    system("apt list --upgradable  >> {}".format(filename))
    with open(filename) as listing:
        for i in listing.readlines()[1:]:
            package = i.split()[0]
            # print('FULL', package.split(' '))
            Upgrade.objects.create(
                name=package.split("/")[0],
                full_name=str(package.split(" ")[0]),
                current_version=i.split()[3:][2][:-1],
                new_version=i.split()[1],
            )
    # # Ansible play for apt update on all servers
    BASE = settings.BASE_DIR
    ANSIBLE_TMP = os.path.join(BASE, "tmp/files")
    ANSIBLE_FILE = "{}/programmed_update_{}.yml".format(
        ANSIBLE_TMP, "Upgrade {}".format(str(timezone.now()))
    )

    play_source = [
        dict(
            name="{}".format(str(ANSIBLE_FILE)),
            hosts="all",
            gather_facts=False,
            become=True,
            become_method="sudo",
            become_user="root",
            tasks=[
                dict(
                    action=dict(module="apt", args={"update_cache": "yes"}),
                    vars={
                        "become": "yes",
                        "ansible_connection": "ssh",
                        "ansible_user": "stackadmin",
                        "ansible_ssh_pass": "Password1",
                        "ansible_sudo_pass": "Password1",
                    },
                ),
            ],
        )
    ]

    yaml.sort_base_mapping_type_on_output = False
    with open(ANSIBLE_FILE, "w+") as playbuk:
        yaml.dump(play_source, playbuk, default_flow_style=False, sort_keys=False)
    # playbuk.write(yaml.dump(play_source))

    r = ansible_runner.run(
        private_data_dir=ANSIBLE_TMP,
        playbook=ANSIBLE_FILE,
        inventory="/etc/ansible/hosts.d/",
    )  # , module_args='whoami')

    for each_host_event in r.events:
        if each_host_event["event"] == "runner_on_ok":
            print("success")

        if each_host_event["event"] == "runner_on_failed":
            print("failed")

        if each_host_event["event"] == "runner_on_unreachable":
            print("unreachable")
        # print('-->',each_host_event['event'])
