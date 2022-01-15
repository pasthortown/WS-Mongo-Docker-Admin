<?php

namespace App\Http\Middleware;

use App\Utils\Helpers;
use Closure;

class MultiDMZ
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
        Helpers::EstablecerDBName('DMZ');
        return $next($request);
    }

}
