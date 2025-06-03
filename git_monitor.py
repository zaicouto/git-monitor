import os
import time
from pathlib import Path

import winrt.windows.data.xml.dom as dom
import winrt.windows.ui.notifications as notifications
from git import Repo, InvalidGitRepositoryError

# Caminho raiz onde estão seus repositórios Git
ROOT_PATH = Path(os.path.expanduser("~/source"))
CHECK_INTERVAL = 600 * 6  # 60 minutos
# CHECK_INTERVAL = 30  # 30 segundos

APP_ID = "GitMonitor.Notifier"  # Pode ser qualquer identificador único


def is_git_repo(path):
    try:
        _ = Repo(path).git_dir
        return True
    except InvalidGitRepositoryError:
        return False


def check_repo_status(repo_path):
    try:
        repo = Repo(repo_path)
        dirty = repo.is_dirty()
        unpushed = False
        need_pull = False

        if repo.remotes:
            origin = repo.remotes.origin
            origin.fetch()

            branch = repo.active_branch
            behind = list(repo.iter_commits(f"{branch}..origin/{branch}"))
            ahead = list(repo.iter_commits(f"origin/{branch}..{branch}"))

            unpushed = len(ahead) > 0
            need_pull = len(behind) > 0

        if any([dirty, unpushed, need_pull]):
            msg = f"[{repo_path.name}]"
            if need_pull:
                msg += " ⚠️ Precisa de git pull"
            if unpushed:
                msg += " ⬆️ Commits não enviados (push)"
            if dirty:
                msg += " 📝 Mudanças locais não commitadas"
            return msg

        return None  # Tudo certo, não notifica

    except Exception as e:
        return f"[{repo_path.name}] ❌ Erro: {e}"


def notify(title, message):
    # Template do toast
    tstr = f"""
    <toast activationType="foreground">
        <visual>
            <binding template="ToastGeneric">
                <text>{title}</text>
                <text>{message}</text>
            </binding>
        </visual>
    </toast>
    """

    # Cria o objeto XML
    xdoc = dom.XmlDocument()
    xdoc.load_xml(tstr)

    # Cria e envia a notificação
    notifier = notifications.ToastNotificationManager.create_toast_notifier(APP_ID)
    notification = notifications.ToastNotification(xdoc)
    notifier.show(notification)


def monitor_git_repos():
    while True:
        attention_needed = []

        for subdir in ROOT_PATH.iterdir():
            if subdir.is_dir() and is_git_repo(subdir):
                result = check_repo_status(subdir)
                if result:
                    attention_needed.append(result)

        if attention_needed:
            for msg in attention_needed:
                notify("Git Monitor", msg)
                print(msg)
        else:
            notify("Git Monitor", "✅ Todos os repositórios estão sincronizados!")
            print("✅ Todos os repositórios estão sincronizados!")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_git_repos()
