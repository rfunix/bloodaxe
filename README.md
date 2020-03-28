![bloodaxe logo](/images/logo.png)

[![CircleCI](https://circleci.com/gh/rfunix/bloodaxe.svg?style=svg)](https://circleci.com/gh/rfunix/bloodaxe)

`bloodaxe` is the nice way to testing and metrifying api flows.

![GIF demo](images/demo.gif)

**Usage**
---

```
Usage: bloodaxe.py [OPTIONS] CONFIG_FILE

Options:
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.

  --help                Show this message and exit.
```
`$ bloodaxe example.toml`

**Installation Options**
---

Install with [`pip`](https://pypi.org/project/bloodaxe/)

`$ pip install bloodaxe`

`$ bloodaxe`

**Flow configuration examples**
---
```toml
[configs]
number_of_concurrent_flows = 10
duration = 60

[[api]]
name = "user_api"
base_url = "http://127.0.0.1:8080"
[api.envvars]
client_id = "CLIENT_ID"
client_secret = "CLIENT_SECRET"

[[api]]
name = "any_api"
base_url = "http://127.0.0.1:1010"

[[request]]
name = "get_token"
url = "{{ user_api.base_url }}/token/"
method = "POST"
timeout = 60
save_result = true
[request.data]
client_id = "{{ user_api.client_id }}"
client_secret = "{{ user_api.client_secret }}"
[request.headers]
Content-Type = 'application/x-www-form-urlencoded'

[[request]]
name = "get_user"
url = "{{ user_api.base_url }}/users/1"
method = "GET"
timeout = 60
save_result = true
[request.headers]
Authorization = "{{ get_token.access_token}}"

[[request]]
name ="get_user_with_params"
url = "{{ user_api.base_url }}/users/"
method = "GET"
timeout = 60
save_result = false
[request.params]
name = "{{ get_user.name }}"
[request.headers]
Authorization = "{{ get_token.access_token}}"

[[request]]
name = "create_new_user"
url = "{{  user_api.base_url }}/users/"
method = "POST"
[request.data]
firstname = "{{ get_user.firstname }} teste"
lastname = "{{ get_user.Lastname }} teste"
status = "{{ get_user.status }} teste"
[request.headers]
Authorization = "{{ get_token.access_token}}"

[[request]]
name = "create_new_user_with_from_file"
url = "{{  user_api.base_url }}/users/"
method = "PATCH"
[request.data]
from_file = "user.json"
[request.headers]
Authorization = "{{ get_token.access_token}}"
```

**Backlog**
---

* Add retry config for request
* Add response status check
* Add response header check
* Add response body check
* Add command to generate imagem diagram flow based in toml file
* Request with 1-n relations
