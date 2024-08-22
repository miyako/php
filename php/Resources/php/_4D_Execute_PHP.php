<?php
/**
 * executePHP
 *
 * Execute the script specified by the "PHP Execute" 4D command
 * Usage:
 * 	$boolOK:=PHP Execute(_4D_ScriptPath, [_4D_ScriptPath, _4D_FunctionName [, _4D_FastCGI_result [, _4D_FastCGI_param_{n} ]]])
 * Example:
 * <code>
 * // Note that this is 4D language code
 *  $boolOK:=PHP Execute(/Volumes/Disk/Folder/ExifThings.php", "GetExifInfos", $result, $imagePath)
 * </code>
 *
 * A "php.ini" file SHOULD set 'display_errors' to 'stderr' for better error handling by 4D
 * It might set others error config as defined by this documentation :
 * @see http://www.php.net/manual/en/errorfunc.configuration.php
 *
 * @since 4D v12
 * @version $Id$
 * @category PHP
 * @copyright Copyright (c) 2010 4D SAS (http://www.4d.com)
 *
 * */

// Won't do anything if not called from 4D.
// Always use getenv() because in some case $_ENV is not populated.

//$pathLogFile = join(DIRECTORY_SEPARATOR, array("C:","Perforce","4D_main_cont_64","4eDimension","main","4D","Tests","PHP","cyril"));
//if (!is_dir($pathLogFile)) {
 //   mkdir($pathLogFile);
//}
//$logFile = join(DIRECTORY_SEPARATOR, array($pathLogFile,"result_".date("YmdHis")."_log.txt")); 
    
//file_put_contents($logFile, "_4D_IsCalledFrom4D\t:\t".strval(getenv('_4D_IsCalledFrom4D'))."\n", FILE_APPEND);
    
if (getenv('_4D_IsCalledFrom4D') === 'yes')
{
	try
	{
		$path=getenv('_4D_ScriptPath');
        //file_put_contents($logFile, "_4D_ScriptPath\t\t:\t".strval($path)."\n", FILE_APPEND);
		if ($path === FALSE)
		{
			throw new Exception('Script not defined!');
		}
		else
		{
			// For Windows platform only:
			// Retrieve the UTF-8 encoded path to the script file ($_ENV['_4D_ScriptPath']).
			// It is hence possible to use non ASCII characters (accent, japanese, etc) in paths.
			// However, php doesn't use unicode but the current code page of Windows.
			// So do the conversion and then overwrite PATH_TRANSLATED with it.

            //file_put_contents($logFile, "_4D_IsWindows\t\t:\t".strval(getenv('_4D_IsWindows'))."\n", FILE_APPEND);
			if (getenv('_4D_IsWindows') === 'yes')
			{
				$windowsCodePage = getenv('_4D_WindowsCodePage');
                //file_put_contents($logFile, "_4D_WindowsCodePage\t:\t".strval(getenv('_4D_WindowsCodePage'))."\n", FILE_APPEND);
				if ($windowsCodePage === FALSE)
				{
					// For backward compatibility, mb_convert_encoding() will have same behavior as utf8_decode().

					$windowsCodePage = 'ISO-8859-1';
				}
                //file_put_contents($logFile, "_4D_WindowsCodePage\t:\t".strval(getenv('_4D_WindowsCodePage'))."\n", FILE_APPEND);
				// If used with an "external" PHP interpreter without support for mbstring, then use utf8_decode().

                //file_put_contents($logFile, "mb_convert_encoding exist\t:\t".strval(function_exists('mb_convert_encoding'))."\n", FILE_APPEND);
				if (function_exists('mb_convert_encoding'))
				{
					$path = mb_convert_encoding($path, $windowsCodePage, 'UTF-8');
				}
				else
				{
					$path = utf8_decode($path);
				}
                
                //file_put_contents($logFile, "path\t\t\t:\t".strval($path)."\n", FILE_APPEND);
				unset($windowsCodePage);
			}
		}
        
        //file_put_contents($logFile, "_4D_Process\t\t:\t".strval(getenv('_4D_Process'))."\n", FILE_APPEND);
		// Get 4D session
		if (getenv('_4D_Process') !== FALSE)
		{
			session_id(getenv('_4D_Process'));
			session_start();
		}
		// send output data to a buffer
		ob_start();
        //file_put_contents($logFile, "path\t\t\t:\t".strval($path)."\n", FILE_APPEND);
		if ($path != 'php_command')
		{
			if (!file_exists($path))
			{
				throw new Exception('Script not found!');
			}
			// execute php script
			// First, update the include_path, so a script using relative path will still execute properly
			set_include_path( get_include_path() . PATH_SEPARATOR . dirname($path) );
            //file_put_contents($logFile, "include_path\t\t\t:\t".strval(get_include_path() . PATH_SEPARATOR . dirname($path))."\n", FILE_APPEND);

			// Then go to the parent directory of the script file.
			// This is to make sure that getcwd() always behaves in CGI "mode": The working directory
			// is where the script file is, and not where the command is invoked (CLI mode).
			// php-fcgi-4d is compiled as CGI but this will make sure it always works properly.
			chdir(dirname($path));

			require $path;
		}
		else
		{
			// If invoking just a function, then go the parent directory of _4D_Execute_PHP.php.
			chdir(dirname(__FILE__));
            //file_put_contents($logFile, "chdir\t\t\t:\t".strval(dirname(__FILE__))."\n", FILE_APPEND);
		}
		unset($path);

        //file_put_contents($logFile, "_4D_FunctionName\t:\t".strval(getenv('_4D_FunctionName'))."\n", FILE_APPEND);
        
		// if a function name is specified call it with its potentials parameters
		if (getenv('_4D_FunctionName') !== FALSE && getenv('_4D_FunctionName') !== '')
		{
            
            //file_put_contents($logFile, "_4D_FunctionName exist\t:\t".strval(function_exists(getenv('_4D_FunctionName')))."\n", FILE_APPEND);
			if (!function_exists(getenv('_4D_FunctionName')))
			{
				throw new Exception('Function not found!');
			}
			$_4D_FunctionName = mb_convert_encoding(getenv('_4D_FunctionName'), "UTF-8", mb_detect_encoding(getenv('_4D_FunctionName'))); //utf8_decode(getenv('_4D_FunctionName')); utf8_decode deprecated since php8.2

            //file_put_contents($logFile, "_4D_FunctionName utf8_decode\t:\t".strval($_4D_FunctionName)."\n", FILE_APPEND);
            
			// get the parameters
			// Values are passed by 4D UTF-8 encoded (this is what json_decode() expects)
            //file_put_contents($logFile, "_4D_FunctionParams\t:\t".strval(getenv('_4D_FunctionParams'))."\n", FILE_APPEND);
			if (getenv('_4D_FunctionParams') === FALSE)
			{
				throw new Exception('Function parameter(s) undefined!');
			}
			$_4D_FastCGI_params = json_decode(getenv('_4D_FunctionParams'));
            //file_put_contents($logFile, "_4D_FastCGI_params\t:\t".strval($_4D_FastCGI_params)."\n", FILE_APPEND);
			if(($_4D_FastCGI_params == '') && (getenv('_4D_FunctionParams') !== ''))
			{
				throw new Exception('Bad JSON encoding for function parameters!');
			}

			// call the function and get the result
      if ($_4D_FastCGI_params == NULL)
        $_4D_FastCGI_params = array();
			if(count($_4D_FastCGI_params) > 0)
			{
				$_4D_FastCGI_result = call_user_func_array($_4D_FunctionName, $_4D_FastCGI_params);
			}
			else
			{
				$_4D_FastCGI_result = call_user_func($_4D_FunctionName);
			}
            //file_put_contents($logFile, "_4D_FastCGI_result\t:\t".strval($_4D_FastCGI_result)."\n", FILE_APPEND);
			// send the result to 4D
            
            //file_put_contents($logFile, "Is_Result_Scalar\t:\t".strval(is_scalar($_4D_FastCGI_result))."\n", FILE_APPEND);
			if (is_scalar($_4D_FastCGI_result))
				$_4D_Encoded_result = $_4D_FastCGI_result;
			else
				$_4D_Encoded_result = json_encode( $_4D_FastCGI_result);
            
            //file_put_contents($logFile, "Encoded Result\t:\t".strval($_4D_Encoded_result)."\n", FILE_APPEND);
			header("X-4D-FunctionResult: " . strtr( base64_encode($_4D_Encoded_result), "\n\r", '  '));
		}
	}
	catch (Exception $_4D_FastCGI_error)
	{
		/**
		 * All catched exception are sent to 4D with all details
		 **/
		header('X-4DPHP-Error-Message: ' . utf8_encode($_4D_FastCGI_error->getMessage()));
		header('X-4DPHP-Error-Code: ' . $_4D_FastCGI_error->getCode());
		header('X-4DPHP-Error-File: ' . utf8_encode($_4D_FastCGI_error->getFile()));
		header('X-4DPHP-Error-Line: ' . $_4D_FastCGI_error->getLine());
		header('X-4DPHP-Error-Trace: ' . json_encode($_4D_FastCGI_error->getTraceAsString()));
		if (method_exists($_4D_FastCGI_error, 'getSeverity'))
		{
			// severity require a try because this method only exists for error exceptions
			header('X-4DPHP-Error-Severity: ' . $_4D_FastCGI_error->getSeverity());
		}
	}
	ob_end_flush();

	// Explicitely exit() because php.ini has a auto_prepend_file setting of this particular script

    //file_put_contents($logFile, "Exit\n\n", FILE_APPEND);
	exit(0);
}

    //file_put_contents($logFile, "\n", FILE_APPEND);
