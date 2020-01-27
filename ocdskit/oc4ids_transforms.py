import copy

import jsonpointer

from ocdskit.combine import merge


def run_transforms(config, releases, project_id=None, compiled_releases=None, output=None):

    """
    Transforms a list of OCDS releases into a OC4IDS project.

    :param dict config: contains optional tranform options.
    :param list releases: list of OCDS releases
    :param string project_id: project ID of resulting project
    :param list compiled_releases: pre computed list of compiled releases
    :param dict output: initial project output template project where transformed data will be added
    """


    transforms = [InitialTransformState(config, releases, project_id, compiled_releases, output)]
    for transform_cls in transform_cls_list:
        transform = transform_cls(transforms)
        transforms.append(transform)

    return transform.output


class InitialTransformState:

    def __init__(self, config, releases, project_id=None, compiled_releases=None, records=None, output=None):
        self.config = config
        self.releases = releases
        self.project_id = project_id
        self.records = records

        if not records:
            self.records = next(merge(self.releases, return_package=True, use_linked_releases=True)).get('records', [])

        compiled_releases = []
        for record in self.records:
            compiled_release = record.get('compiledRelease', {})
            # projects only have linked releases 'uri' is a good proxy for that.
            linked_releases = [release for release in record.get('releases', []) if release.get('uri')]
            embeded_releases = [release for release in record.get('releases', []) if not release.get('uri')]

            compiled_release['releases'] = linked_releases
            compiled_release['embededReleases'] = embeded_releases

            compiled_releases.append(compiled_release)


        self.compiled_releases = compiled_releases
        self.output = output or {}
        if project_id and 'id' not in self.output:
            self.output['id'] = project_id
        self.success = True


class BaseTransform:

    def __init__(self, last_transforms):
        last_transform = last_transforms[-1]
        self.last_transforms = last_transforms
        self.config = last_transform.config
        self.releases = last_transform.releases
        self.compiled_releases = last_transform.compiled_releases
        self.output = last_transform.output
        self.last_transform_success = last_transform.success
        self.success = False

        self.run()

    def run(self):
        pass

    def copy_party_by_role(self, role, new_roles=None):

        for compiled_release in self.compiled_releases:
            parties = compiled_release.get('parties', [])
            if not isinstance(parties, list):
                continue
            for party in compiled_release.get('parties', []):
                if role in party.get('roles', []):
                    output_parties = self.output.get('parties', [])  
                    if not output_parties:
                        self.output['parties'] = output_parties
                    output_party = copy.deepcopy(party)
                    if new_roles:
                        output_roles = output_party.get('roles', [])
                        output_roles.extend(new_roles)
                        output_party['roles'] = output_roles
                    output_parties.append(output_party)
                    self.success = True


class PublicAuthorityRole(BaseTransform):
    def run(self):
        self.copy_party_by_role('publicAuthority')


class BuyerRole(BaseTransform):
    def run(self):
        if self.config.get('copy_buyer_role'):
            self.copy_party_by_role('buyer', ['publicAuthority'])
        else:
            self.success = True


class Sector(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            sector = jsonpointer.resolve_pointer(compiled_release, '/planning/project/sector', None)
            if sector:
                self.output['sector'] = sector
                self.success = True
                break


class AdditionalClassifications(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            additionalClassifications = jsonpointer.resolve_pointer(
                compiled_release, '/planning/project/additionalClassifications', None
            )
            if additionalClassifications:
                self.output['additionalClassifications'] = additionalClassifications
                self.success = True
                break


class Title(BaseTransform):
    def run(self):
        for compiled_release in self.compiled_releases:
            title = jsonpointer.resolve_pointer(compiled_release, '/planning/project/title', None)
            if title:
                self.output['title'] = title
                self.success = True
                break


class TitleFromTender(BaseTransform):
    def run(self):
        if not self.config.get('use_tender_title'):
            self.success = True
            return
        if self.last_transforms[-1].success:
            self.success = True
            return

        for compiled_release in self.compiled_releases:
            title = jsonpointer.resolve_pointer(compiled_release, '/tender/title', None)
            if title:
                self.output['title'] = title
                self.success = True
                break



transform_cls_list = [
    PublicAuthorityRole,
    BuyerRole,
    Sector,
    AdditionalClassifications,
    Title,
    TitleFromTender
]
