```bash
# ideally make a virtual envrionment first
# with python -m venv ~/ENV3
# source ~/ENV3/bin/activate
pip install -U "huggingface_hub[cli]"
git config --global credential.helper store

huggingface-cli login
# go to  https://huggingface.co/settings/tokens
# and make a token with write perms
# yes, save as git credential

sudo usermod -aG docker $USER

sudo apt update
sudo apt install -y nvidia-container-runtime

sudo systemctl daemon-reload
sudo systemctl restart docker
``` 