<?php

namespace App\Http\Middleware;

use App\Utils\Helpers;
use Closure;
use Illuminate\Support\Facades\Config;

class MultiDB
{
    /**
     * Handle an incoming request.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \Closure  $next
     * @return mixed
     */
    public function handle($request, Closure $next)
    {
        $dbname=$request->route('dbname');
        Helpers::EstablecerDBName($dbname);
        return $next($request);
    }

}
