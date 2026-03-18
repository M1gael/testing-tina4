# TINA4 Testing

## Ruby

**Installation** 
- Had a stuggle getting correct tina4 to execute, an easy solution would be language specific trails:
```shell
tina4-ruby init myDir

tina4-py init myDir

tina4-js init myDir
```

For now use :
```shell
$(ruby -e 'print Gem.bin_path("tina4", "tina4")') start
```



**Routing**
- Routes are registered twice during initialization. This is visible in the console output when starting the server:
```text
[DEBUG] Route registered: GET /test-auto
[DEBUG] Route registered: GET /test-render
...
[DEBUG] Route registered: GET /test-auto
[DEBUG] Route registered: GET /test-render
```


**POST Security**
- POST/PUT/PATCH/DELETE routes are secured by default, returning a 403 Forbidden error if no authentication is provided. This is consistent with the Python port but may be unexpected for Ruby developers used to open routes by default.
```text
HTTP/1.1 403 Forbidden
```
- Resolved by explicitly setting `auth: false` in the route definition.
**Middleware (Hooks)**
- `Tina4.before` and `Tina4.after` hooks are correctly registered in the `Middleware` class, but they are **never executed** in the current `RackApp` implementation. This prevents any pre-request or post-request logic (like logging, global header injection, etc.) from running.
```ruby
# myroute.rb
Tina4.before do |request, response|
  Tina4::Debug.info("Middleware: Request received") # This never appears in logs
end
```

**Database / ORM**
- The `init` command creates a project structure but does not include necessary database driver gems (like `sqlite3`, `pg`, `mysql2`) in the `Gemfile`. Attempting to use the database fails with a `LoadError` during initialization.
```text
LoadError: cannot load such file -- sqlite3
```
- Developers must manually add these dependencies to their `Gemfile`.

**Migrations**
- Empty migration files (or files containing only comments) are marked as successful `[OK]` and recorded in the migrations table. This can lead to silent failures where a developer thinks a table was created but it wasn't because the file was empty or had a syntax error that didn't stop execution.
