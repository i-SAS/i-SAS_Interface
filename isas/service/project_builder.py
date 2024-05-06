import os
import shutil
import warnings
from pathlib import Path

import yaml


class ProjectBuilder:
    def __init__(
            self,
            cfg: dict,
            project_dir: Path,
            ) -> None:
        """Initialize ProjectBuilder.

        Args:
            cfg: A config of the project.
            project_dir: A path to the directory for building project.
        """
        self.cfg = cfg
        self.project_dir = project_dir
        shutil.rmtree(self.project_dir, ignore_errors=True)
        self.project_dir.mkdir()

    def __call__(self) -> None:
        """Build i-SAS project."""
        self._create_project_dir()
        self._create_service_dirs()

    def _create_project_dir(self) -> None:
        """Create project directory and compose.yml"""
        ports = {
            service_name: service_cfg['PORT']
            for service_name, service_cfg in self.cfg['SERVICES'].items()
            }
        project_name = os.getenv('PROJECT_NAME')
        docker_compose = {
            'services': {
                service_name: self._construct_service_compose(service_name, service_cfg, project_name, ports)
                for service_name, service_cfg in self.cfg['SERVICES'].items()
                },
            'networks': {
                'default': {
                    'name': self.cfg['NETWORK']['NETWORK_NAME'],
                    'external': self.cfg['NETWORK'].get('EXTERNAL', False),
                    },
                },
            'volumes': {
                f'project-{project_name}_volume': None,
                },
            }
        with (self.project_dir / 'compose.yml').open('w') as f:
            yaml.safe_dump(docker_compose, f, sort_keys=False)

        for filename in ('.env', ):
            shutil.copy(f'./{filename}', self.project_dir / filename)

    def _construct_service_compose(
            self,
            service_name: str,
            service_cfg: dict,
            project_name: str,
            ports: dict,
            ) -> dict:
        """Construct service configuration.

        Args:
            service_name: The name of a service.
            service_cfg: The configration of a service.
            project_name: The name of the project
            ports: A dict whose the key is service_name and the value is port number.

        Returns:
            A dict containing service configurations.
        """
        res = {
            'image': f'isas_project-{project_name}:system',
            'container_name': f'project-{project_name}_system_{service_name}',
            'command': 'poetry run isas_run cfg/service.yml',
            'volumes': [
                f'./{service_name}:/root/workspace',
                f'project-{project_name}_volume:/root/datadrive',
                ],
            'environment': [
                f'SERVICE_NAME={service_name}',
                f'PORT={";".join([f"{k}:{v}" for k, v in ports.items()])}',
                ],
            'env_file': ['.env'],
            'ports': list(ports.values()),
            }
        return res

    def _create_service_dirs(self) -> None:
        """Create service directories in the project directory."""
        for service_name, service_cfg in self.cfg['SERVICES'].items():
            service_dir = self.project_dir / service_name
            service_dir.mkdir()
            (service_dir / 'cfg').mkdir()
            with (service_dir / 'cfg/service.yml').open('w') as f:
                yaml.safe_dump(service_cfg, f, sort_keys=False)
            filenames = ['pyproject.toml']
            if service_cfg['SERVICE_TYPE'] == 'Dashboard':
                filenames.append('src/content_layout.py')
            for filename in filenames:
                if not Path(filename).exists():
                    warnings.warn(f'{filename} does not exist. This might occur error when running the project.')
                    continue
                file_path = service_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(filename, file_path)
