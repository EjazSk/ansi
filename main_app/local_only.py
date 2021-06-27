import yaml
import os

from django.db import transaction
from django.conf import settings

import ansible_runner
from celery import shared_task

from .models import Upgrade, UpgradeResultDetails
from .models import Upgrade
from .utils import get_patch_data
from .models import UpgradeResult


@shared_task
def py_ansible_runner_local(name, packages):
    groups = "local"
    tasks=[]
    upgrade_result = UpgradeResult.objects.create(
        name="{}".format(str(name)), status="In Process", groups=groups
    )
    for package in packages:
        task = dict(
            action=dict(module="package", args={"name": package, "state": "latest"}),
            vars={
                "become": "yes",
                "ansible_connection": "ssh",
                "ansible_user": settings.ANSIBLE_USER,
                "ansible_ssh_pass": settings.ANSIBLE_PASSWORD,
                "ansible_sudo_pass": settings.ANSIBLE_PASSWORD,
            },
        )
        tasks.append(task)

    print("-------In Local----------------")

    # Combine all packages to tasks
    BASE = settings.BASE_DIR
    ANSIBLE_TMP = os.path.join(BASE, "tmp/files")
    ANSIBLE_FILE = "{}/programmed_local{}.yml".format(ANSIBLE_TMP, str(name))

    play_source = [
        dict(
            name="{}".format(str(name)),
            hosts=groups,
            gather_facts=False,
            become=True,
            become_method="sudo",
            become_user="root",
            tasks=tasks,
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

    try:

        print(upgrade_result.pk)
        for each_host_event in r.events:
            if (
                each_host_event["event"] == "runner_on_ok"
                and "name"
                in each_host_event["event_data"]["res"]["invocation"]["module_args"]
            ):
                # print('on ok')
                # creating entry for Upgraded Patch

                # Patch process
                patch = Upgrade.objects.filter(
                    name=str(
                        each_host_event["event_data"]["res"]["invocation"][
                            "module_args"
                        ]["name"]
                    )
                )

                if patch.exists():
                    patch = Upgrade.objects.get(
                        name=str(
                            each_host_event["event_data"]["res"]["invocation"][
                                "module_args"
                            ]["name"]
                        )
                    )

                    # Create Upgraded patch object

                else:
                    patch = Upgrade(
                        name=str(
                            each_host_event["event_data"]["res"]["invocation"][
                                "module_args"
                            ]["name"]
                        ),
                        current_version=0,
                        new_version=0,
                    )
                check_already_exist = UpgradeResultDetails.objects.filter(
                    uuid=each_host_event["uuid"]
                )
                if not check_already_exist:

                    upgrade_result.save()
                    UpgradeResultDetails.objects.create(
                        upgrade_result=upgrade_result,
                        uuid=each_host_event["uuid"],
                        pid=each_host_event["pid"],
                        event=each_host_event["event"],
                        host=each_host_event["event_data"]["host"],
                        state=each_host_event["event_data"]["res"]["invocation"][
                            "module_args"
                        ]["state"],
                        changed=each_host_event["event_data"]["res"]["changed"],
                        start_time=each_host_event["event_data"]["start"],
                        end_time=each_host_event["event_data"]["end"],
                        duration=each_host_event["event_data"]["duration"],
                        resp_dump=each_host_event["event_data"]["res"],
                        runner_result="SUCCESS",
                        package=str(
                            each_host_event["event_data"]["res"]["invocation"][
                                "module_args"
                            ]["package"]
                        ),
                        package_name=str(
                            each_host_event["event_data"]["res"]["invocation"][
                                "module_args"
                            ]["name"]
                        ),
                        last_version=str(patch.current_version),
                        upgraded_version=str(patch.current_version),
                    )

                transaction.commit()
            elif each_host_event["event"] == "runner_on_unreachable":

                check_already_exist = UpgradeResultDetails.objects.filter(
                    uuid=each_host_event["uuid"]
                )
                if not check_already_exist:

                    upgrade_result.save()
                    UpgradeResultDetails.objects.create(
                        upgrade_result=upgrade_result,
                        uuid=each_host_event["uuid"],
                        pid=each_host_event["pid"],
                        event=each_host_event["event"],
                        host=each_host_event["event_data"]["host"],
                        state=each_host_event["event_data"]["res"]["unreachable"],
                        changed=each_host_event["event_data"]["res"]["changed"],
                        start_time=each_host_event["event_data"]["start"],
                        end_time=each_host_event["event_data"]["end"],
                        duration=each_host_event["event_data"]["duration"],
                        resp_dump=each_host_event["event_data"]["res"],
                        msg=each_host_event["event_data"]["res"]["msg"],
                        runner_result="NOT REACHABLE",
                    )

            elif each_host_event["event"] == "runner_on_failed":

                check_already_exist = UpgradeResultDetails.objects.filter(
                    uuid=each_host_event["uuid"]
                )
                if not check_already_exist:
                    # upgrade_result.unreachable_count = str(
                    #     int(upgrade_result.unreachable_count) + 1)
                    upgrade_result.save()
                    UpgradeResultDetails.objects.create(
                        upgrade_result=upgrade_result,
                        uuid=each_host_event["uuid"],
                        pid=each_host_event["pid"],
                        event=each_host_event["event"],
                        host=each_host_event["event_data"]["host"],
                        state=each_host_event["event_data"]["res"]["invocation"][
                            "module_args"
                        ]["state"],
                        changed=each_host_event["event_data"]["res"]["changed"],
                        start_time=each_host_event["event_data"]["start"],
                        end_time=each_host_event["event_data"]["end"],
                        duration=each_host_event["event_data"]["duration"],
                        resp_dump=each_host_event["event_data"]["res"],
                        msg=each_host_event["event_data"]["res"]["msg"],
                        runner_result="FAILED",
                    )

        upgrade_result.status = "Completed"
        print("BEFORE PATCH CALL")
        get_patch_data()
        print("AFTER PATCH CALL")
        upgrade_result.save()

        # return upgrade_result
        # os.remove(ANSIBLE_FILE)
    except Exception as e:
        print("Error ->", e)
        upgrade_result.fail_msg = str(e)
        upgrade_result.status = "Failed"
        upgrade_result.save()
