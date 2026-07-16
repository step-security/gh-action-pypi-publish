import json
import os
import pathlib
import sys
import urllib.request

DESCRIPTION = 'description'
REQUIRED = 'required'

REF = os.environ['REF']
REPO = os.environ['REPO']

ACTION_SHELL_CHECKOUT_PATH = pathlib.Path(__file__).parent.resolve()

# Published image for release v1.14.0
IMAGE_DIGEST = (
    'sha256:d6dd36811cb9ff523b58289782e05fd52861cfa37d34acc2c338bd18e0bfb418'
)

_MANIFEST_ACCEPT = ', '.join((
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
    'application/vnd.docker.distribution.manifest.v2+json',
))


def _ghcr_image_exists(repo: str, digest: str) -> bool:
    # NOTE: Query the registry over HTTPS with an anonymous pull token so the
    # NOTE: check does not depend on Docker experimental features, the buildx
    # NOTE: plugin, or any locally configured registry credentials -- all of
    # NOTE: which vary between runners and caused false negatives that made the
    # NOTE: action rebuild the image from the Dockerfile instead.
    try:
        token_url = (
            'https://ghcr.io/token'
            f'?service=ghcr.io&scope=repository:{repo}:pull'
        )
        with urllib.request.urlopen(token_url, timeout=15) as response:
            token = json.load(response)['token']

        manifest_request = urllib.request.Request(
            f'https://ghcr.io/v2/{repo}/manifests/{digest}',
            method='HEAD',
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': _MANIFEST_ACCEPT,
            },
        )
        with urllib.request.urlopen(manifest_request, timeout=15) as response:
            return response.status == 200
    except Exception as exc:
        print(
            f'::warning::Could not confirm ghcr.io/{repo}@{digest} '
            f'({type(exc).__name__}: {exc}); falling back to Dockerfile build.',
            file=sys.stderr,
        )
        return False


def set_image(ref: str, repo: str) -> str:
    if _ghcr_image_exists(repo, IMAGE_DIGEST):
        image = f'docker://ghcr.io/{repo}@{IMAGE_DIGEST}'
    else:
        image = str(ACTION_SHELL_CHECKOUT_PATH / 'Dockerfile')
    print(f'::notice::Resolved action image to: {image}', file=sys.stderr)
    return image


image = set_image(REF, REPO)

action = {
    'name': '🏃',
    DESCRIPTION: (
        'Run Docker container to upload Python distribution packages to PyPI'
    ),
    'inputs': {
        'user': {DESCRIPTION: 'PyPI user', REQUIRED: False},
        'password': {
            DESCRIPTION: 'Password for your PyPI user or an access token',
            REQUIRED: False,
        },
        'repository-url': {
            DESCRIPTION: 'The repository URL to use',
            REQUIRED: False,
        },
        'packages-dir': {
            DESCRIPTION: 'The target directory for distribution',
            REQUIRED: False,
        },
        'verify-metadata': {
            DESCRIPTION: 'Check metadata before uploading',
            REQUIRED: False,
        },
        'skip-existing': {
            DESCRIPTION: (
                'Do not fail if a Python package distribution'
                ' exists in the target package index'
            ),
            REQUIRED: False,
        },
        'verbose': {DESCRIPTION: 'Show verbose output.', REQUIRED: False},
        'print-hash': {
            DESCRIPTION: 'Show hash values of files to be uploaded',
            REQUIRED: False,
        },
        'attestations': {
            DESCRIPTION: (
                ' Enable support for PEP 740 attestations.'
                ' Only works with PyPI and TestPyPI via Trusted Publishing.'
            ),
            REQUIRED: False,
        },
    },
    'runs': {
        'using': 'docker',
        'image': image,
    },
}

# The generated trampoline action must exist in the allowlisted
# runner-defined working directory so it can be referenced by the
# relative path starting with `./`.
#
# This mutates the end-user's workspace slightly but uses a path
# that is unlikely to clash with somebody else's use.
#
# We cannot use randomized paths because the composite action
# syntax does not allow accessing variables in `uses:`. This
# means that we end up having to hardcode this path both here and
# in `action.yml`.
action_path = pathlib.Path(
    '.github/.tmp/.generated-actions/'
    'run-pypi-publish-in-docker-container/action.yml',
)
action_path.parent.mkdir(parents=True, exist_ok=True)
action_path.write_text(json.dumps(action, ensure_ascii=False), encoding='utf-8')
