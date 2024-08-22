# _CGI

`_CGI` is a class for managing local CGI instances in a worker. Extend this class to control a specific CGI program. The CGI should use be launched as a `_CLI` instance.

## .new() 

**.new**($name : Text) : cs._CGI

`$name` will be the worker name spawned to start the CGI. The callee process need not be a worker. The name is also used as a global semaphore to prevent the creation of multiple instance of the same CGI.

Properties:

|Property|Type|Description|
|:-|:-|:-|
|name|Text|unique name that identifies the CGI (read-only)|

## .expand() 

**.expand**($in : Object) : Object

Expand a file system path of a `4D.File` or `4D.Folder` to a platform path suitable for the command line interface.

## .quote() 

**.quote**($in : Text) : Text

Double-quote a path string.

## .start() 

**.start**($function : 4D.Function)

Invoke `$function` in a worker `This.name` with a global semaphore. The function should launch the CGI and return an instance of `_CLI`. The instance is stored in a process variable in the worker's execution context and used to terminate the CGI in `This.stop()`.

## .stop() 

**.stop**()

Invoke `4D.SystemWorker.terminate()` with a global semaphore. 