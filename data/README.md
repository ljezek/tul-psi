# PSI Team Configuration

## Instructions

1. Fork the https://github.com/ljezek/tul-psi/ repository ([guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo?tool=webui)).
2. In your favourite IDE (VS Code recommended) clone your fork of the repository to your local machine ([guide](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)).
   * `git clone https://github.com/[YOUR-NAME]/tul-psi.git`
3. Create your feature branch.
   * `git checkout -b feature/[MY-BRANCH]`
4. Add your project definition to the [`projects.json`](./projects.json) - include project name, GitHub repo URL and your own user entry.
5. Commit and push your changes to your feature branch.
   * `git commit -a -m 'Define [MY AWESOME PROJECT] for PSI 2026'`
   * `git push` - publishes the branch to your fork of the repo
6. Give your teammates *Write* access to your forked repo ([add collaborator guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-your-project/managing-access-to-your-projects#managing-access-for-user-level-projects)).
7. Your teammates clone the repo on their machines & switch to your branch (see 2 & 3 above).
8. Your teammates add themselves to your shared project and commit & push (see 5).
   * Keep the projects and team members sorted alphabetically by name.
9. After your team is complete, one member creates a Pull Request to integrate your change into the `main` branch of the [official repo](https://github.com/ljezek/tul-psi/) ([guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)).

### Conflict resolution

In case there are conflicts (when merging to official `tul-psi` repo), you need to fetch the remote changes into your feature branch:

* `git remote add upstream https://github.com/ljezek/tul-psi.git`
* `git fetch upstream`
* `git checkout feature/add-team-xyz`
* `git rebase upstream/main`
* If there's a conflict, open the [`projects.json`](./projects.json) file and resolve the conflict in your favourite editor (remove the `<<<<<<<, =======, >>>>>>>` conflict markers and keep data of all projects and members in the right order).
   * Continue rebasing by `git add data/projects.json && git rebase --continue`
* Commit and push new version of the feature branch.

### Projects.json structure

The [`projects.json`](./projects.json) configuration file stores academic years, project definitions and their members.

Please keep entries in all the lists alphabetically sorted by their name (i.e., projects by `project_name` and members by `name`).

Example definition of projects.json:

```json
{
  "2026": [
    {
      "project_name": "Lectors - Student Projects Catalogue",
      "github_repo_url": "https://github.com/ljezek/tul-psi",
      "members": [
        {
          "name": "Lukáš Ježek",
          "github_alias": "ljezek",
          "tul_email": "lukas.jezek@tul.cz"
        },
        {
          "name": "Roman Špánek",
          "github_alias": "roman-spanek",
          "tul_email": "roman.spanek@tul.cz"
        }
      ]
    },
    {
        "project_name": "My awesome project",
        "github_repo_url": "https://github.com/myalias/my-awesome-project",
        "members": [
            // Add your members here
        ]
    }
  ]
}