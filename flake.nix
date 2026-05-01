{
  description = "A Nix-flake-based Python development environment";

  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1";

  # Point this at your real config/dev-tools flake.
  # Examples:
  # inputs.devtools.url = "github:overtoneblue/Dendritic-Nixland";
  # inputs.devtools.url = "path:/home/cenunix/Dendritic-Nixland";
  inputs.devtools.url = "github:overtoneblue/nixos-config";

  outputs =
    {
      self,
      nixpkgs,
      devtools,
      ...
    }:

    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forEachSupportedSystem =
        f:
        nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            inherit system;
            pkgs = import nixpkgs { inherit system; };
          }
        );

      version = "3.13";
    in
    {
      devShells = forEachSupportedSystem (
        { pkgs, system }:
        let
          concatMajorMinor =
            v:
            pkgs.lib.pipe v [
              pkgs.lib.versions.splitVersion
              (pkgs.lib.sublist 0 2)
              pkgs.lib.concatStrings
            ];

          python = pkgs."python${concatMajorMinor version}";
        in
        {
          default = pkgs.mkShellNoCC {
            venvDir = ".venv";

            packages = [
              # Your configured Git wins over transitive git-minimal.
              (pkgs.lib.hiPrio devtools.packages.${system}.myGit)
            ]
            ++ (with python.pkgs; [
              venvShellHook
              pip
              requests
              python-dotenv
              streamlit
              sqlalchemy
            ])
            ++ [
              pkgs.git-filter-repo
              pkgs.fd
              pkgs.ripgrep
              pkgs.eza
              pkgs.bat
              pkgs.zoxide
              pkgs.fzf
              pkgs.btop
              self.formatter.${system}
            ];

            shellHook = ''
                            export EDITOR=nvim
                            export VISUAL=nvim

                            venvVersionWarn() {
                              local venvVersion
                              venvVersion="$("$venvDir/bin/python" -c 'import platform; print(platform.python_version())')"

                              [[ "$venvVersion" == "${python.version}" ]] && return

                              cat <<EOF
              Warning: Python version mismatch: [$venvVersion (venv)] != [${python.version}]
                       Delete '$venvDir' and reload to rebuild for version ${python.version}
              EOF
                            }

                            venvVersionWarn
            '';
          };
        }
      );

      formatter = forEachSupportedSystem ({ pkgs, ... }: pkgs.nixfmt);
    };
}
