{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
    in
      {
         devShell = pkgs.mkShell {
           buildInputs = with pkgs; [
             uv
             act
             docker
           ];

           LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath [
           ]}:$LD_LIBRARY_PATH";


           shellHook = ''
             export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
             '';
         };
      }
  );

}
