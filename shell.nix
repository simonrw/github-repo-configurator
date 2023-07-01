{ pkgs ? import <nixpkgs> {} }:
with pkgs;

let
  my-python = python311;

  pythonPackages = python311.pkgs;
in

mkShell {
  buildInputs = [
    my-python
    pythonPackages.venvShellHook
  ];
  venvDir = ".venv";
}
