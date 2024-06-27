import os
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def __init__(self, path):
        self.path = path
        self.permissions_backup = os.path.join(path, 'permissions_backup.txt')
        self.save_icacls()
        self.permissions = self.get_permissions()
        print(f"Initial permissions:\n{self.permissions}")

    def get_permissions(self):
        permissions = {}
        for dirpath, dirnames, filenames in os.walk(self.path):
            for name in dirnames + filenames:
                full_path = os.path.join(dirpath, name)
                try:
                    permissions[full_path] = self.get_icacls(full_path)
                except FileNotFoundError:
                    continue
        return permissions

    def get_icacls(self, path):
        result = subprocess.run(['icacls', path], capture_output=True, text=True)
        return result.stdout.strip()

    def save_icacls(self):
        # Save the permissions to a file
        result = subprocess.run(['icacls', self.path, '/save', self.permissions_backup, '/t'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Permissions saved to {self.permissions_backup}")
        else:
            print(f"Failed to save permissions, error: {result.stderr}")

    def restore_icacls(self):
        # Restore the permissions from the backup file
        parent_dir = os.path.dirname(self.path)
        result = subprocess.run(['icacls', parent_dir, '/restore', self.permissions_backup], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Permissions restored for {parent_dir} from {self.permissions_backup}")
        else:
            print(f"Failed to restore permissions for {parent_dir}, error: {result.stderr}")

    def check_permission_changes(self):
        current_permissions = self.get_permissions()
        for path, perms in current_permissions.items():
            if path not in self.permissions:
                # New file detected, record its permissions
                self.permissions[path] = perms
                print(f"New file detected: {path} with permissions:\n{perms}")
                continue
            if self.permissions[path] != perms:
                print(f"Permission change detected in: {path}")
                self.restore_icacls()
        self.permissions = current_permissions

    def on_any_event(self, event):
        self.check_permission_changes()

def main():
    path = r"C:\Users\FLASH_596\Projects\permission manager\check"  # The directory to be monitored
    event_handler = MyHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print("Monitoring started (Press Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
