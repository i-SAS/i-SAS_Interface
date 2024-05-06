from pathlib import Path

import yaml

from isas.service import ProjectBuilder


def main() -> None:
    cfg_path = Path('./cfg/project.yml')
    with cfg_path.open('r') as f:
        cfg = yaml.safe_load(f)

    project_dir = Path('./project_system')
    builder = ProjectBuilder(cfg, project_dir)
    builder()


if __name__ == '__main__':
    main()
