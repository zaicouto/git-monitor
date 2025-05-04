import os
import time
from pathlib import Path

from git import Repo, InvalidGitRepositoryError
from win10toast import ToastNotifier

# Caminho raiz onde estão seus repositórios Git
ROOT_PATH = Path(os.path.expanduser("~/source"))
CHECK_INTERVAL = 600 * 6  # 60 minutos

toaster = ToastNotifier()


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
            behind = list(repo.iter_commits(f'{branch}..origin/{branch}'))
            ahead = list(repo.iter_commits(f'origin/{branch}..{branch}'))

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


def notify(message):
    toaster.show_toast(
        "Git Monitor",
        message,
        duration=10
    )
    while toaster.notification_active():
        time.sleep(0.1)


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
                notify(msg)
                print(msg)
        else:
            notify("✅ Todos os repositórios estão sincronizados!")
            print("✅ Todos os repositórios estão sincronizados!")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_git_repos()
