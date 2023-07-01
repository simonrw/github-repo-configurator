{ pkgs ? import <nixpkgs> {} }:
with pkgs;

let
  my-python = python311;

  pythonPackages = my-python.pkgs;
in

mkShell {
  buildInputs = [
    my-python
    pythonPackages.venvShellHook
  ];
  venvDir = ".venv";
}
