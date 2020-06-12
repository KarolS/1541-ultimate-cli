# 1541 Ultimate CLI

A command-line tool and library for remote controlling 1541 Ultimate II+.

## Requirements

* Python 3.6 or newer

## Usage

    python u1541.py <IP address> <command>

where 

* `<IP address>` is the IP address of the Ultimate.

* `<command>` is a command as described below

In the following examples:

* `<local path>` is the path to a file on the local computer.

* `<remote path>` is the path to a file on the Ultimate. The path usually starts with `/Usb0/`

>

    run <remote path>
    
Run a program file (*.prg) on the C64.    

    mount <remote path>
    
Mount a disk image file (*.d64).    

    upload <local paths> <remote path>
    
Upload one or more files into the Ultimate.
If there are more than one local file, then remote path is treated as a directory.
Existing files will be overwritten.

    ur <local path> <remote path>
    
Upload a program file (*.prg) into the Ultimate and then immediately run it on the C64.
Existing files will be overwritten.

    um <local path> <remote path>
    
Upload a disk image file (*.d64) into the Ultimate and then immediately mount it.
Existing files will be overwritten.

    download <remote paths>
    
Download files from the Ultimate into the current directory

    dir <remote path>
    
List files in the directory on the Ultimate.
If remote directory is not specified, defaults to `/Usb0`.

    reu <REU size>

Set REU size (use `0` to disable). Size range: `128K` to `16M`.

    shell

Starts an interactive shell. You can use the above commands in the shell.
Enter `help` to list all commands, `quit` to quit. 

## License

MIT. See [License](./LICENSE).
