{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});
    git-moduletree = system:
      pkgs.${system}.stdenv.mkDerivation {
        name = "git-moduletree";
        dontUnpack = true;
        version = "0.1.0";
        buildInputs = [pkgs.${system}.git pkgs.${system}.python312];
        installPhase = ''
          install -Dm755 ${./git-moduletree} $out/bin/git-moduletree
          install -Dm755 ${./git-moduletree-prototype.py} $out/bin/git-moduletree-prototype.py
        '';
      };
  in {
    packages = forAllSystems (system: {
      default = git-moduletree system;
    });

    devShells = forAllSystems (system: {
      default = pkgs.${system}.mkShell {
        packages = [
          (git-moduletree system)
        ];
      };
    });
  };
}
