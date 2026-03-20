{ pkgs }: {
  deps = [
    pkgs.nodejs-18_x
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.bash
  ];
}
