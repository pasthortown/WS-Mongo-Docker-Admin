<?php

namespace App\Http\Middleware;

use App\Utils\Helpers;
use Closure;

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
        $token = $request->header('token');
        if(!$token) {
            return response()->json([
                'error' => 'Token no recibido.'
            ], 401);
        }
        $token_validated = Helpers::Autenticar($token);
        if ($token_validated) {
            $dbname=$request->route('dbname');
            Helpers::EstablecerDBName($dbname);
            return $next($request);
        } else {
            return response()->json([
                'error' => 'Token no válido'
            ], 400);
        }

    }

}
