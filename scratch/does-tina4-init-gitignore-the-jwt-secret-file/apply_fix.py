# Deterministically turn a stock src/init.rs into the fixed one. Every
# substitution is asserted unique, so a silent no-op cannot masquerade as a pass.
import sys
p=sys.argv[1]; s=open(p).read()
edits=[
 ('".venv/\\n__pycache__/\\n*.pyc\\n*.pyo\\ndata/\\nlogs/\\nsecrets/\\n.env\\n"',
  '".venv/\\n__pycache__/\\n*.pyc\\n*.pyo\\ndata/\\nlogs/\\nsecrets/\\n.env\\n.env.local\\n"'),
 ('"vendor/\\ndata/\\nlogs/\\ncache/\\nsecrets/\\n.env\\n"',
  '"vendor/\\ndata/\\nlogs/\\ncache/\\nsecrets/\\n.env\\n.env.local\\n"'),
 ('".bundle/\\nvendor/\\ndata/\\nlogs/\\n.env\\nGemfile.lock\\n"',
  '".bundle/\\nvendor/\\ndata/\\nlogs/\\n.env\\n.env.local\\nGemfile.lock\\n"'),
 ('"node_modules/\\ndist/\\ndata/\\nlogs/\\n.env\\n"',
  '"node_modules/\\ndist/\\ndata/\\nlogs/\\n.env\\n.env.local\\n"'),
]
for old,new in edits:
    assert s.count(old)==1, f"template anchor not unique: {old[:44]}"
    s=s.replace(old,new,1)
anchor='''    #[test]
    fn tina4js_scaffold_uses_the_current_framework_release() {'''
assert s.count(anchor)==1, "test anchor not unique"
t='''    #[test]
    fn scaffold_gitignores_the_dev_secret_file() {
        // On its first dev run the framework mints a JWT signing secret and
        // writes it to .env.local. Every backend scaffold must ignore that file
        // or the secret is committable — .env does not cover .env.local.
        // The sentinel is a line unique to that language's own template, so the
        // test also fails if the dispatcher routes a language to the wrong one.
        for (lang, sentinel) in [
            ("python", ".venv/"),
            ("php", "cache/"),
            ("ruby", "Gemfile.lock"),
            ("nodejs", "node_modules/"),
        ] {
            let dir = std::env::temp_dir()
                .join(format!("tina4_init_ignore_{lang}_{}", std::process::id()));
            let _ = fs::remove_dir_all(&dir);
            fs::create_dir_all(&dir).unwrap();
            scaffold_project(lang, dir.to_str().unwrap());
            let ignored = fs::read_to_string(dir.join(".gitignore"))
                .expect("scaffold wrote a .gitignore");
            assert!(
                ignored.lines().any(|l| l.trim() == sentinel),
                "{lang} must get its own template (sentinel {sentinel}), got:\\n{ignored}"
            );
            assert!(
                ignored.lines().any(|l| l.trim() == ".env.local"),
                "{lang} .gitignore must ignore .env.local, got:\\n{ignored}"
            );
            let _ = fs::remove_dir_all(&dir);
        }
    }

'''
s=s.replace(anchor,t+anchor,1)
open(p,'w').write(s)
print("fix applied")
