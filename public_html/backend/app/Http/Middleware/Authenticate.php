<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Contracts\Auth\Factory as Auth;
use Exception;
use Firebase\JWT\JWT;
use Firebase\JWT\ExpiredException;

use App\Utils\Helpers;
use Illuminate\Support\Facades\Config;

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
        Helpers::EstablecerDBName('Auth');
        $token = $request->header('token');
        if(!$token) {
            return response()->json([
                'error' => 'Token no recibido.'
            ], 401);
        }
        try {
            $payload = JWT::decode($token, env('JWT_SECRET'), ['HS256']);
            $timeRemaining = $payload->expiration_time - time();
            if ($timeRemaining <= 0) {
                return response()->json([
                    'error' => 'Token caducado.'
                ], 400);
            }
        } catch(ExpiredException $e) {
            return response()->json([
                'error' => 'Token caducado.'
            ], 400);
        } catch(Exception $e) {
            return response()->json([
                'error' => 'Token no válido'
            ], 400);
        }
        $user = DB::collection(env('ACCOUNTS_DB'))
                ->where('token',$token)
                ->first();
        if (!$user) {
            return response()->json([
                'error' => 'Token no válido'
            ], 400);
        }
        $request->payload = $payload;
        $request->user = $user;
        return $next($request);
        // VALIDAR SI EL TOKEN PRESENTADO ES EL OTORGADO
    }

}
