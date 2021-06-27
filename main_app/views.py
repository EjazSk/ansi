import time
from django.shortcuts import render, redirect
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.contrib.messages import warning
from formtools.wizard.views import SessionWizardView
from django.contrib.messages import success

from .utils import get_patch_data
from .models import Server, ServerGroup, Upgrade, UpgradeResult
from .forms import (
    CreateServerForm,
    CreateGroupForm,
    PatchForm,
    NodeGroupForm,
    PatchNameForm,
)
from .tasks import py_ansible_runner
from .local_only import py_ansible_runner_local


def home(request):
    return render(request, "home.html", {})


class ServerListView(ListView):
    template_name = "server_list.html"
    queryset = Server.objects.all()
    context_object_name = "servers"


class ServerDetailView(DetailView):
    template_name = "server_detail.html"
    queryset = Server.objects.all()
    context_object_name = "server"


class CreateServerView(SuccessMessageMixin, CreateView):
    template_name = "create_server.html"
    form_class = CreateServerForm
    success_message = "Server %(name)s created successfully"


class UpdateServerView(SuccessMessageMixin, UpdateView):
    # redirect_to = 're'
    template_name = "create_server.html"
    queryset = Server.objects.all()
    form_class = CreateServerForm
    success_message = "Server %(name)s updated successfully"


class DeleteServerView(SuccessMessageMixin, DeleteView):
    template_name = "delete_server.html"
    queryset = Server.objects.all()
    context_object_name = "server"
    success_message = "Server %(name)s deleted successfully"
    success_url = reverse_lazy("servers")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        warning(self.request, self.success_message % obj.__dict__)
        return super(DeleteServerView, self).delete(request, *args, **kwargs)


class GroupListView(ListView):
    template_name = "group_list.html"
    queryset = ServerGroup.objects.all()
    context_object_name = "groups"


class GroupDetailView(SuccessMessageMixin, DetailView):
    queryset = ServerGroup.objects.all()
    template_name = "group_detail.html"
    context_object_name = "group"


class CreateGroupView(SuccessMessageMixin, CreateView):
    template_name = "group_form.html"
    form_class = CreateGroupForm


class GroupUpdateView(SuccessMessageMixin, UpdateView):
    queryset = ServerGroup.objects.all()
    template_name = "group_form.html"
    form_class = CreateGroupForm


class GroupDeleteView(DeleteView):
    queryset = ServerGroup.objects.all()
    template_name = "group_delete.html"
    success_url = reverse_lazy("groups")
    context_object_name = "group"


class UpgradeListView(ListView):
    template_name = "upgrade_list.html"
    queryset = Upgrade.objects.all()
    context_object_name = "upgrades"

    def post(self, request):
        get_patch_data()
        print("Refreshing...")
        success(request, "Refreshed successfully!")
        return redirect("upgrades")


class UpgradeWizard(SessionWizardView):
    template_name = "upgrade_wizad.html"
    form_list = [PatchForm, NodeGroupForm, PatchNameForm]

    def done(self, form_list, **kwargs):
        all_packages, groups, play_name = [form.cleaned_data for form in form_list]
        # Name for the play/result
        name = play_name["name"]
        # Extract current as well as upgraded packages name and combining them
        packages = all_packages["patches"]
        packages = [package.name for package in packages]
        packages = packages
        # Selected groups concatinated to be a single string
        groups = groups["servers"]
        groups = ",".join(group.name for group in groups)
        print("groups", groups)
        print("packages", packages)
        print("name", name)

        py_ansible_runner_local(name, packages)
        # py_ansible_runner.delay(groups, packages, name)
        time.sleep(2)
        return redirect(reverse("upgrades"))


class UpgradeResultView(ListView):
    template_name = "upgrade_result_list.html"
    queryset = UpgradeResult.objects.all()
    context_object_name = "results"


class UpgradeResultDetailView(DetailView):
    template_name = "upgrade_result_detail.html"
    queryset = UpgradeResult.objects.all()
    context_object_name = "result"
