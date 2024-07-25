# Run this as admin to change permissions for everyone to prevent read write errors to projects in folder for the AI
import os
import stat
import subprocess
import sys

def check_and_set_permissions(folder_name='projects'):
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the path to the projects folder
    projects_folder = os.path.join(current_dir, folder_name)
    
    print(f"Checking permissions for: {projects_folder}")
    
    # Ensure the folder exists
    os.makedirs(projects_folder, exist_ok=True)
    
    if sys.platform.startswith('win'):
        # Windows-specific commands
        try:
            # Remove read-only attribute
            subprocess.run(['attrib', '-R', projects_folder], check=True, shell=True)
            print("Read-only attribute removed (if it existed)")
            
            # Set full control for everyone (use with caution)
            subprocess.run(['icacls', projects_folder, '/grant', 'Everyone:(OI)(CI)F', '/T'], check=True, shell=True)
            print("Full control permissions set for everyone")
        except subprocess.CalledProcessError as e:
            print(f"Error setting permissions: {e}")
    else:
        # Unix-like systems (Linux, macOS)
        try:
            # Set read, write, and execute permissions for owner, group, and others
            os.chmod(projects_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            print("Full permissions set for everyone")
        except Exception as e:
            print(f"Error setting permissions: {e}")
    
    # Recursively set permissions for all subdirectories and files
    for root, dirs, files in os.walk(projects_folder):
        for dir in dirs:
            check_and_set_permissions(os.path.join(root, dir))
        for file in files:
            try:
                os.chmod(os.path.join(root, file), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
            except Exception as e:
                print(f"Error setting permissions for file {file}: {e}")

    print("Permissions check and set completed")

if __name__ == "__main__":
    check_and_set_permissions()