import yaml
from jinja2 import Environment, FileSystemLoader

def main():
    # 1. Load YAML schema + ownership config
    with open("websubmit.yml") as f:
        data = yaml.safe_load(f)

    tables = data["tables"]

    # 2. Set up Jinja environment to look inside templates/
    env = Environment(loader=FileSystemLoader("templates"))

    # 3. Render K9db schema SQL from k9db.j2
    schema_tmpl = env.get_template("k9db.j2")
    schema_sql = schema_tmpl.render(tables=tables)

    with open("generated_k9db.sql", "w") as f:
        f.write(schema_sql)

    # 4. Render Sesame policy YAML from sesame.j2
    policies_tmpl = env.get_template("sesame.j2")
    policies_yaml = policies_tmpl.render(tables=tables)

    with open("generated_sesame.yml", "w") as f:
        f.write(policies_yaml)

    print("Generated: generated_k9db.sql and generated_sesame.yml")

if __name__ == "__main__":
    main()
