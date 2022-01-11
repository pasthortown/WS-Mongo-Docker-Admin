<?php

namespace App\Utils;

use Illuminate\Support\Facades\Config;

class Helpers {

    public static function EstablecerDBName($dbname){
        Config::set('database.connections.mongodb.database', $dbname);
    }
}
