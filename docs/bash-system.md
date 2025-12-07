## GitHub and Some Structure Initialization
```bash
cd ~
ssh-keygen -t ed25519 -C "ec2-aws-etc-key"    # press Enter through prompts

# Show the public key
cat ~/.ssh/id_ed25519.pub
```
Copy that output → add it to GitHub → Settings → SSH and GPG keys → New SSH key.

Then:
```bash
# If origin already exists, this will replace it
git remote remove origin 2>/dev/null || true
git remote add origin git@github.com:Fruitful-Network-Development/aws-etc.git

# Pull the main branch into GH-etc
git pull origin main
```

## Set up GH-etc as the dedicated system-files repo
```bash
cd ~/GH-etc
git init
git remote add origin git@github.com:Fruitful-Network-Development/aws-etc.git
git pull origin main
```

## Build the aws/etc structure (local mirror of system files)
```bash
cd ~/aws

# Create etc/systemd/system
mkdir -p etc/systemd/system

# Create etc/nginx with basic subdirs
mkdir -p etc/nginx/sites-available etc/nginx/sites-enabled

# Create empty placeholder files for now (you'll sync or copy real ones later)
touch etc/systemd/system/platform.service
touch etc/nginx/nginx.conf
touch etc/nginx/mime.types
```

## Create aws/srv/webapps structure
```bash
cd ~/aws

# Base dirs
mkdir -p srv/webapps
mkdir -p srv/webapps/clients

```

## Set up platform repo under aws/srv/webapps/platform
  - Two options again: clone directly or init + set remote.
  - Recommended: clone directly
```bash
cd ~/aws

git clone git@github.com:Fruitful-Network-Development/flask-app.git srv/webapps/platform
# Or HTTPS:
# git clone https://github.com/Fruitful-Network-Development/flask-app.git srv/webapps/platform
```

## Set up client repos under aws/srv/webapps/clients/...
### Fruitful Network Development
```bash
cd ~/aws

git clone git@github.com:Fruitful-Network-Development/web-dir-fnd.git \
  srv/webapps/clients/fruitfulnetworkdevelopment.com

# Or HTTPS:
# git clone https://github.com/Fruitful-Network-Development/web-dir-fnd.git \
#   srv/webapps/clients/fruitfulnetworkdevelopment.com
```

### Cuyahoga Terra Vita
```bash
cd ~/aws

git clone git@github.com:Fruitful-Network-Development/web-dir-ctv.git \
  srv/webapps/clients/cuyahogaterravita.com

# Or HTTPS:
# git clone https://github.com/Fruitful-Network-Development/web-dir-ctv.git \
#   srv/webapps/clients/cuyahogaterravita.com
```

## Create the aws/etc structure
Now let’s build the supporting files tree you described under ~/aws:
```bash
cd ~/aws

# Create etc/systemd/system
mkdir -p etc/systemd/system

# Create etc/nginx with typical layout
mkdir -p etc/nginx/sites-available etc/nginx/sites-enabled
touch etc/nginx/nginx.conf
touch etc/nginx/mime.types

# Create placeholder platform.service (we can overwrite it from GH-etc later)
touch etc/systemd/system/platform.service

```
### (Optional but probably what you want) Copy real configs from GH-etc
If your aws-etc repo already has real Nginx and systemd files (likely at etc/nginx and etc/systemd/system inside GH-etc), you can mirror them into your aws/etc sandbox instead of leaving placeholders.
```bash
cd ~/

# Copy Nginx configs from GH-etc into aws/etc
if [ -d GH-etc/etc/nginx ]; then
  cp -r GH-etc/etc/nginx/* aws/etc/nginx/
fi

# Copy systemd units from GH-etc into aws/etc
if [ -d GH-etc/etc/systemd/system ]; then
  cp -r GH-etc/etc/systemd/system/* aws/etc/systemd/system/
fi
```

## NEXT SECTION

### Install Missing Tools
```bash
sudo apt-get update

# Install dig (dnsutils) and rsync
sudo apt-get install -y dnsutils rsync
```

### run the DNS check
```bash
dig +short fruitfulnetworkdevelopment.com
dig +short cuyahogaterravita.com
```

### Sync your modeled webapps into the live location
Now that rsync is installed, re-do the sync:
```bash
cd ~

# Ensure live webapps dir exists
sudo mkdir -p /srv/webapps

# Sync modeled webapps into live path
sudo rsync -av ~/aws/srv/webapps/ /srv/webapps/
```


### Make sure Nginx is using your configs (not the default page)
```bash
cd ~

# Make sure Nginx directories exist
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

# Copy your main config and mime.types
sudo cp ~/aws/etc/nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp ~/aws/etc/nginx/mime.types /etc/nginx/mime.types

# Copy your site configs
sudo cp ~/aws/etc/nginx/sites-available/*.conf /etc/nginx/sites-available/
```

Disable the default Nginx site (this is what’s giving you “Welcome to nginx!”):
```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

Enable your two domains:
```bash
sudo ln -sf /etc/nginx/sites-available/fruitfulnetworkdevelopment.com.conf \
            /etc/nginx/sites-enabled/fruitfulnetworkdevelopment.com.conf

sudo ln -sf /etc/nginx/sites-available/cuyahogaterravita.com.conf \
            /etc/nginx/sites-enabled/cuyahogaterravita.com.conf
```

#### Test and Reload
```bash
sudo nginx -t
```
If it says syntax is ok and test is successful, run:
```bash
sudo systemctl reload nginx
```

HERE
```bash
HERE
```

HERE
```bash
HERE
```

HERE
```bash
HERE
```

HERE
```bash
HERE
```
