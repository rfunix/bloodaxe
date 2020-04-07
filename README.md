[![CircleCI](https://circleci.com/gh/rfunix/bloodaxe.svg?style=svg)](https://circleci.com/gh/rfunix/bloodaxe)


![bloodaxe logo](/images/logo.png)

`bloodaxe` is the nice way to testing and metrifying api flows.

![GIF demo](images/demo.gif)

**Usage**
---

```
Usage: bloodaxe.py [OPTIONS] CONFIG_FILE

Options:
  --verbose / --no-verbose
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
number_of_concurrent_flows = 10 # Number of concurrent coroutines flows
duration = 60 # Stressing duration

[[api]] # Api context
name = "user_api"
base_url = "http://127.0.0.1:8080" # Base url at the moment, is the unique parameter in api section.
[api.envvars] # Environment variables for given api
client_id = "CLIENT_ID" # Envvars names
client_secret = "CLIENT_SECRET"

[[api]]
name = "any_api"
base_url = "http://127.0.0.1:1010"

[[request]] # Request context
name = "get_token" 
url = "{{ user_api.base_url }}/token/" # Use user_api context to get the base_url
method = "POST"
timeout = 60 # The bloodaxe default timeout value is 10 secs, but it's possible override the default value
save_result = true # Save request result in request name context, default value is false
[request.data] # Request data section
client_id = "{{ user_api.client_id }}" # templating syntax is allowed in request.data
client_secret = "{{ user_api.client_secret }}"
[request.headers] # Request header section
Content-Type = 'application/x-www-form-urlencoded'

[[request]]
name = "get_user"
url = "{{ user_api.base_url }}/users/1"
method = "GET"
timeout = 60
save_result = true
[request.headers]
Authorization = "{{ get_token.access_token}}" # templating syntax is allowed in request.headers

[[request]]
name ="get_user_with_params"
url = "{{ user_api.base_url }}/users/"
method = "GET"
timeout = 60
save_result = false
[request.params] # Request params section
name = "{{ get_user.name }}" # templating syntax is allowed in request.params/querystring
[request.headers]
Authorization = "{{ get_token.access_token}}"

[[request]]
name = "create_new_user"
url = "{{  user_api.base_url }}/users/"
method = "POST"
[request.data]
firstname = "{{ get_user.firstname }} test"
lastname = "{{ get_user.Lastname }} test"
status = "{{ get_user.status }} test"
[request.headers]
Authorization = "{{ get_token.access_token}}"
[request.response_check] # response_check feature checking response data and status_code
status_code = 201
[request.response_check.data]
firstname = "{{ get_user.firstname }} test" # templating syntax is allowed in response data checks
lastname = "{{ get_user.Lastname }} test"
status = "{{ get_user.status }} test"

[[request]]
name = "create_new_user_with_from_file"
url = "{{  user_api.base_url }}/users/"
method = "PATCH"
[request.data]
from_file = "user.json" # from_file help you configure request.data
[request.headers]
Authorization = "{{ get_token.access_token}}"
```

**Backlog**
---
https://github.com/rfunix/bloodaxe/projects/1
