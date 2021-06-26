from django.urls import path

from .views import (
    home,
    ServerListView,
    ServerDetailView,
    CreateServerView,
    DeleteServerView,
    UpdateServerView,
    GroupListView,
    GroupDetailView,
    CreateGroupView,
    GroupUpdateView,
    GroupDeleteView,
    UpgradeListView,
    UpgradeWizard,
    UpgradeResultView,
    UpgradeResultDetailView,
)

urlpatterns = [
    path("", home, name="home"),
    path("servers/", ServerListView.as_view(), name="servers"),
    path("servers/create", CreateServerView.as_view(), name="create-server"),
    path("servers/<int:pk>/", ServerDetailView.as_view(), name="server-detail"),
    path("servers/<int:pk>/edit", UpdateServerView.as_view(), name="server-edit"),
    path("servers/<int:pk>/delete", DeleteServerView.as_view(), name="server-delete"),
    path("groups/", GroupListView.as_view(), name="groups"),
    path("groups/create/", CreateGroupView.as_view(), name="create-group"),
    path("group/<int:pk>/", GroupDetailView.as_view(), name="group-detail"),
    path("group/<int:pk>/edit/", GroupUpdateView.as_view(), name="group-edit"),
    path("group/<int:pk>/delete/", GroupDeleteView.as_view(), name="group-delete"),
    path("upgrades/", UpgradeListView.as_view(), name="upgrades"),
    path("upgrades/upgrade", UpgradeWizard.as_view(), name="upgrade"),
    path("results/", UpgradeResultView.as_view(), name="results"),
    path("results/<int:pk>/", UpgradeResultDetailView.as_view(), name="result-detail"),
]
