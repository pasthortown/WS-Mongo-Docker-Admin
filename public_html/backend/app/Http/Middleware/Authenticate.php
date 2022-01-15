<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Contracts\Auth\Factory as Auth;

use App\Utils\Helpers;

class Authenticate
{
    /**
     * The authentication guard factory instance.
     *
     * @var \Illuminate\Contracts\Auth\Factory
     */
    protected $auth;

    /**
     * Create a new middleware instance.
     *
     * @param  \Illuminate\Contracts\Auth\Factory  $auth
     * @return void
     */
    public function __construct(Auth $auth)
    {
        $this->auth = $auth;
    }

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
            return $next($request);
        } else {
            return response()->json([
                'error' => 'Token no válido'
            ], 400);
        }
    }

}
