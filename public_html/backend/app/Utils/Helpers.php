<?php

namespace App\Utils;

use Illuminate\Support\Facades\Config;
use Firebase\JWT\JWT;
use Firebase\JWT\ExpiredException;
use Illuminate\Support\Facades\DB;
use Exception;

class Helpers {

    public static function EstablecerDBName($dbname){
        Config::set('database.connections.mongodb.database', $dbname);
    }

    public static function Autenticar($token) {
        try {
            $payload = JWT::decode($token, env('JWT_SECRET'), ['HS256']);
            $timeRemaining = $payload->expiration_time - time();
            if ($timeRemaining <= 0) {
                return false;
            }
        } catch(ExpiredException $e) {
            return false;
        } catch(Exception $e) {
            return false;
        }
        return true;
    }
}
