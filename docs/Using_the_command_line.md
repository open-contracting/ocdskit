# Using the command line

Pretty print:

    python -m json.tool filename.json

Read the first 1000 bytes of a file:

    head -c 1000 filename.json

Add newlines to ends of files (Fish shell):

    for i in *.json; echo >> $i; end

On Windows, you may need to install [Cygwin](http://cygwin.com.) to use some command-line tools. PowerShell has [some corresponding tools](http://xahlee.info/powershell/PowerShell_for_unixer.html).
