<?php
/*===================================================+
|| # ___                  _              _ _
|| # |   \ _____ __ ___ _ | |___  __ _ __| | |_ _
|| # | |) / _ \ V  V / ' \| / _ \/ _` / _` | | '_|
|| # |___/\___/\_/\_/|_||_|_\___/\__,_\__,_|_|_|
|| #
|+===================================================+
|| # Downloadlr WAPI (WebAPI)
|| # REL 01.03.00.01
|| # All rights reserved.
|| # https://www.igorgiovannini.ch
|+===================================================*/

require_once '../vendor/autoload.php';
Predis\Autoloader::register();

class Media {
  public $url = "";
  public $status = 0;
  public $token = "";
  public $expiration = null;
  public $type = "";
  public $toQueue = true;

  public function __construct($url, $token, $mediaType) {
    $this->url = $url;
    $this->token = $token;
    $this->type = $mediaType;
  }

  public function expose() {
    return get_object_vars($this);
  }
}

function getFileName($token) {
  $files = scandir('/downloads');
  foreach($files as $file) {
    if(strlen($file) > 32 && substr($file, 0, 32) == $token) {
      return $file;
    }
  }
  return null;
}

function getMediaUsingToken($token) {
  try {
    $redis = new Predis\Client();
    $iteration = new Predis\Collection\Iterator\Keyspace($redis);

    foreach ($iteration as $key) {
      if($key == $token) {
        return json_decode($redis->get($key), true);
      }
    }
    return null;
  }
  catch (Exception $e) {
    die($e->getMessage());
  }
}

function generateToken($url, $mediaType) {
    return md5($url.$mediaType);
}


$app = new Slim\App;

$app->get('/Server/status', function ($request, $response) {
  $myObject['working'] = "ok";
  return $response->withJson($myObject)->withHeader('Content-Type', 'application/json');
});

$app->post('/Media', function ($request, $response, $args) {
    $url = $request->getParam('u', null);
    $mediaType = $request->getParam('mediaType', null);

    if($url != null && $mediaType != null) {
      $token = generateToken($url, $mediaType);
      $media = getMediaUsingToken($token);
      if($media == null) {
        $media = new Media($url, $token, $mediaType);
        try {
          $redis = new Predis\Client();
          $redis->set($token, json_encode($media->expose()));
          $myObject['token'] = $media->token;
          return $response->withJson($myObject)->withHeader('Content-Type', 'application/json');
        }
        catch (Exception $e) {
          die($e->getMessage());
        }
      }
      $myObject['token'] = $media->token;
      return $response->withJson($myObject)->withHeader('Content-Type', 'application/json');
    } else {
      throw new Exception("Bad request", 401);
    }
});

$app->get('/Media/{token}', function ($request, $response) {
    $token = $request->getAttribute('token');
    if($token != null && strlen($token) != 0) {
      $media = getMediaUsingToken($token);
      if($media != null) {
        $myObject['status'] = $media['status'];
        $myObject['expiration'] = $media['expiration'];
        if(getFileName($token) != null)
          $myObject['fileSize'] = filesize('/downloads/'.getFileName($token));
        else
          $myObject['fileSize'] = 0;

        return $response->withJson($myObject)->withHeader('Content-Type', 'application/json');
      } else {
        throw new \Slim\Exception\NotFoundException($request, $response);
      }
    } else {
      throw new Exception("Bad request", 401);
    }
});

$app->get('/Media/{token}/download', function ($request, $response) {
    $token = $request->getAttribute('token');
    if($token != null && strlen($token) != 0) {
      $media = getMediaUsingToken($token);
      if($media != null) {
        $fileName = getFileName($token);
        if(strlen($fileName) > 32) {
          $file = '/downloads/'.$fileName;
          $fh = fopen($file, 'rb');

          $stream = new \Slim\Http\Stream($fh); // create a stream instance for the response body

          return $response->withHeader('Content-Type', 'application/force-download')
                          ->withHeader('Content-Type', 'application/octet-stream')
                          ->withHeader('Content-Type', 'application/download')
                          ->withHeader('Content-Description', 'File Transfer')
                          ->withHeader('Content-Transfer-Encoding', 'binary')
                          ->withHeader('Content-Disposition', 'attachment; filename="' . substr(basename($file), 33) . '"')
                          ->withHeader('Expires', '0')
                          ->withHeader('Cache-Control', 'must-revalidate, post-check=0, pre-check=0')
                          ->withHeader('Pragma', 'public')
                          ->withBody($stream); // all stream contents will be sent to the response
        } else {
          throw new \Slim\Exception\NotFoundException($request, $response);
        }
      } else {
        throw new Exception("Bad request", 401);
      }
    }
});

$app->run();
