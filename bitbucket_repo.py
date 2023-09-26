# -*- encoding: utf-8 -*-
'''
@File    :   bitbucket_repo.py
@Time    :   2023/09/19 11:30:05
@Author  :   liqy-a 
'''

"""Bitbucket code repository."""
import os
import re
from typing import Optional

from zenml.code_repositories import (
    BaseCodeRepository,
    LocalRepositoryContext,
)
from zenml.code_repositories.base_code_repository import (
    BaseCodeRepositoryConfig,
)
from zenml.code_repositories.git.local_git_repository_context import (
    LocalGitRepositoryContext,
)
from zenml.logger import get_logger
from zenml.utils.secret_utils import SecretField

logger = get_logger(__name__)


class BitbucketCodeRepositoryConfig(BaseCodeRepositoryConfig):
    """Config for Bitbucket glodon code repositories.

    Args:
        url: The full URL of the Bitbucket project.
        token: The token to access the repository.
        username: The username of the project, corespond to token
    """
    url: Optional[str]
    token: str = SecretField()
    username: str


class BitbucketCodeRepository(BaseCodeRepository):
    """GitLab code repository."""

    @property
    def config(self) -> BitbucketCodeRepositoryConfig:
        """Returns the `GitLabCodeRepositoryConfig` config.

        Returns:
            The configuration.
        """
        return BitbucketCodeRepositoryConfig(**self._config)

    def login(self) -> None:
        """Logs in to GitLab.

        Raises:
            RuntimeError: If the login fails.
        """
        repo_url = self.config.url.strip().split(":")[1]
        self.url = f"https://{self.config.username}:{self.config.token}@{repo_url}"  
        return None

    def download_files(
        self, commit: str, directory: str, repo_sub_directory: Optional[str]
    ) -> None:
        """Downloads files from a commit to a local directory.

        Args:
            commit: The commit to download.
            directory: The directory to download to.
            repo_sub_directory: The sub directory to download from.
        """
        try:
            os.system(f"git clone --recurse-submodules {self.url} {directory}")
            os.system(f"cd {directory} && git checkout {commit} && cd ..")
        except Exception as e:
            logger.error("Error processing %s: %s", self.config.url, e)

    def get_local_context(self, path: str) -> Optional[LocalRepositoryContext]:
        """Gets the local repository context.

        Args:
            path: The path to the local repository.

        Returns:
            The local repository context.
        """
        return LocalGitRepositoryContext.at(
            path=path,
            code_repository_id=self.id,
            remote_url_validation_callback=self.check_remote_url,
        )

    def check_remote_url(self, url: str) -> bool:
        """Checks whether the remote url matches the code repository.

        Args:
            url: The remote url.

        Returns:
            Whether the remote url is correct.
        """
        https_url = self.config.url
        if url == https_url:
            return True
        # project + repo_name, ep: /cv/chatglm-finetune.git
        repo_name = https_url.split("scm")[-1]
        ssh_regex = re.compile(
            f".*glodon.com:7999{repo_name}"
        )
        if ssh_regex.fullmatch(url):
            return True

        return False
