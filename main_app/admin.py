from django.contrib import admin

from .models import Server, ServerGroup, UpgradeResult, Upgrade, UpgradeResultDetails

admin.site.register(Server)
admin.site.register(ServerGroup)
admin.site.register(Upgrade)
admin.site.register(UpgradeResult)
admin.site.register(UpgradeResultDetails)
