# AGENT OPERATING INSTRUCTIONS

Purpose: These guidelines ensure agents do not break the server or overwrite live files.  
All changes must be made through the `aws-box` repository and proposed via MCP pull requests.

---

## 1. Accessing Supporting Files (Read-Only)

### Configuration sandbox
All system and Nginx config files live in:
```
/home/admin/aws-box
```
This is the only directory that represents system configuration.  
You may read and modify files *in this directory only*, and only via GitHub pull requests.

### Deployed platform & client sites (strictly read-only)
- Backend Flask API:  
  `/srv/webapps/platform`
- FND frontend:  
  `/srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend`
- CTV frontend:  
  `/srv/webapps/clients/cuyahogaterravita.com/frontend`

These paths represent deployed code.  
**Never write to these directories.**  
Do not run `git init`, `git remote add`, or modify files here.

### Live system configuration (strictly read-only)
Files under `/etc` or `/srv/webapps` are written only via deploy scripts.  
You may read them but **never modify them directly**.

### Audit outputs
Audit scripts write text files to:
```
/home/admin/aws-box/docs/audit/
```
You may read these logs to understand server state.  
Never modify log contents.

---

## 2. Making Changes Safely

### Propose new scripts
If you need the server to perform an action, write a new script within:
```
aws-box/scripts/
```
and submit a pull request using the MCP tool.

### Update existing scripts via PR
If an audit or deployment script must be changed, modify it inside `aws-box/scripts`  
and submit a pull request.  
Never edit live server files.

### Never push from the server
Agents must **never run `git push` from the EC2 instance**.  
All pushes happen via MCP-initiated GitHub pull requests.

### No direct system edits
Do NOT modify:
- `/etc/nginx/nginx.conf`
- files in `/etc/systemd/system`
- any live service configuration

These are always synced from `aws-box` during deployment.

### No system administration commands
Agents must NOT:
- install packages  
- restart services  
- alter firewall rules  
- manage users  
- modify ports or network bindings  

If such changes are required, propose a script.

### Focus on analysis
Agents should:
- read audit logs  
- inspect GH‑etc configuration  
- generate improvement suggestions  
- submit PRs containing updated scripts or configuration files  

---

## 3. Architecture Rules (Critical)

1. **`aws-box` is the only writable config repo.**  
2. **`/etc` and `/srv` are always read-only when accessed by agents.**  
3. **All changes must be versioned and reviewed through GitHub.**  
4. **Nothing modifies the server directly except approved scripts.**

---

## 4. Rebuild Workflow

When a new EC2 instance is launched:

1. A human sets environment variables  
2. A human runs the deployment script  
3. The server is rebuilt from GitHub and `aws-box`  
4. Agents do *not* configure the server directly

---

These are the required operating instructions for all agents interacting with the Fruitful Network Development server.
