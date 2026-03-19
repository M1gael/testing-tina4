# TINA4 Testing
The goal is to create basic implementations using the frameworks to evaluate their ease of use, performance. And to then report any problems or improvement that can be made in evalframework.md under the relative language section.

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

**Documentation**


**Routing and Templates**
- Setting up routes using the `routes/` directory (e.g., `routes/root.rb` with `Tina4.get(...)`) works smoothly.
- Twig template rendering (e.g. `response.render("mywebsite.twig")`) and extending base layouts works as expected. 
- Static file resolution (e.g. `public/css/test.css`) follows standard, intuitive conventions.

**Execution and Stability**
- Starting the server remains somewhat problematic. Even when resolving the CLI issue via `$(ruby -e 'print Gem.bin_path("tina4", "tina4")') start`, the Puma server process seems to exit immediately or fail to run in the background predictably when initiated from a shell execution environment.
- Directly running `ruby app.rb` also parses routes but simply drops back to the prompt, missing a blocking execution loop to keep the server bound to the port. This leads to `Failed to connect to host` errors when attempting to request endpoints.

**Database and ORM Documentation**
- The "Full Example App" and ORM documentation imply that once you define an ORM class (e.g., `class User < Tina4::ORM` with field definitions), you can immediately execute `User.create` or `user.save`.
- However, the ORM **does not auto-generate tables** based on your schema. Furthermore, attempting to use `.save` or `.create` when the table is missing completely fails **silently**. No exception is thrown, no logs are generated, and execution simply continues, leaving the developer thinking the record was saved when the database is actually empty.
- A developer strictly following the guide will be confused. The documentation should clarify that you *must* also manually create matching migrations for every ORM model before using them with the framework.

**Auto-Initialization and Global State**
- Tina4 forces auto-scaffolding the exact moment you `require "tina4"`. It immediately builds `.env`, `.keys/`, and `logs/` in the *Current Working Directory* of whatever process required the gem.
- This creates severe workspace pollution. Tools like language servers (`ruby-lsp`) or linters running from a parent workspace directory will trigger the scaffolding scripts by simply evaluating the code for autocomplete, littering the developer's root folder with `.env` files and `.keys` directories instead of keeping them contained within the actual application directory.
