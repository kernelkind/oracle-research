{
  description = "Pinned standalone development environment for oracle-mvp";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          cargo
          clang
          clippy
          cmake
          llvmPackages.libclang
          openssl
          pkg-config
          rustc
          rustfmt
          zstd
        ];

        LIBCLANG_PATH = "${pkgs.llvmPackages.libclang.lib}/lib";
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ];
      };
    };
}
