<?php

namespace App\Http\Controllers;

use App\Models\DummyModel;
use Illuminate\Http\Request;
use Firebase\JWT\ExpiredException;
use Exception;
use App\Http\Controllers\Controller;
use Illuminate\Support\Str;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Crypt;
use stdClass;
use Firebase\JWT\JWT;
use Illuminate\Support\Facades\Mail;

class AuthController extends Controller {


    public function login(Request $data) {
        $body = $data->json()->all();
        try {
            $password = $body['password'];
            $email = $body['email'];
            $user = DB::collection(env('ACCOUNTS_DB'))
                ->where('email',$email)
                ->first();
            if (!$user) {
                return response()->json('Acceso no autorizado', 400);
            }
            if (!$user['active']) {
                return response()->json('Cuenta bloqueada por exceso de intentos', 400);
            }
            if ($user['disabled']) {
                return response()->json('Cuenta bloqueada por el administrador', 400);
            }
            if ($password !== Crypt::decryptString($user['password'])) {
                $toUpdate['login_tries'] = $user['login_tries'] + 1;
                if ($toUpdate['login_tries'] == env('MAX_LOGIN_TRIES')) {
                    $toUpdate['active'] = false;
                    $message = 'Cuenta bloqueada por exceso de intentos';
                } else {
                    $message = 'Acceso no autorizado, intentos disponibles '. (env('MAX_LOGIN_TRIES')-$toUpdate['login_tries']);
                }
                $updated = DB::collection(env('ACCOUNTS_DB'))->where('email', $email)->update($toUpdate, ['upsert' => false]);
                return response()->json($message, 400);
            }
            $toUpdate['login_tries'] = 0;
            $token = $this->gen_token($email, env('TOKEN_LIFETIME'));
            $toUpdate['token'] = $token;
            $updated = DB::collection(env('ACCOUNTS_DB'))->where('email', $email)->update($toUpdate, ['upsert' => false]);
            unset($user['password']);
            unset($user['token']);
            $toReturn = new stdClass();
            $toReturn->updated = $updated;
            $toReturn->token = $token;
            $toReturn->user_data = $user;
            return response()->json($toReturn, 200);
        } catch( Exception $e ) {
            return response()->json('Los campos email y password son requeridos', 400);
        }
    }

    public function recovery(Request $data) {
        $email = $data['email'];
        $preview_user = DB::collection(env('ACCOUNTS_DB'))->where('email',$email)->get();
        if (sizeof($preview_user)==0) {
            return response()->json('El correo electrónico proporcionado no se encuentra asociado a cuenta alguna', 400);
        }
        $user_data = $preview_user[0];
        $user_data['recovery_token'] = $this->gen_token($email, env('RECOVERY_TOKEN_LIFETIME'));
        $this->send_email('password_recovery_request', $user_data);
        return response()->json('Solicitud de recuperación de contraseña enviada al correo electrónico proporcionado', 200);
    }

    public function reset_password(Request $data) {
        if(!isset($data['token'])) {
            return response()->json([
                'error' => 'Token no recibido.'
            ], 401);
        }
        $token = $data['token'];
        $payload = JWT::decode($token, env('JWT_SECRET'), ['HS256']);
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
        $email = $payload->email;
        $toUpdate = [];
        $toUpdate['timestamp'] = date('Y-m-d H:i:s');
        $toUpdate['active'] = true;
        $toUpdate['login_tries'] = 0;
        $password = $this->gen_password();
        $toUpdate['password'] = Crypt::encryptString($password);
        $updated = DB::collection(env('ACCOUNTS_DB'))->where('email', $email)->update($toUpdate, ['upsert' => false]);
        if ($updated) {
            $user_data = DB::collection(env('ACCOUNTS_DB'))->where('email', $email)->first();
            $user_data['password'] = $password;
            $this->send_email('password_reset', $user_data);
            return response()->json('Contraseña actualizada satisfactoriamente, la contraseña a sido enviada al correo electrónico del usuario', 200);
        } else {
            return response()->json('Ocurrió un error al resetear la contraseña del usuario', 400);
        }
    }

    public function reset_password_user(Request $data) {
        $id = $data['item_id'];
        $toUpdate = [];
        $toUpdate['timestamp'] = date('Y-m-d H:i:s');
        $toUpdate['active'] = true;
        $toUpdate['login_tries'] = 0;
        $password = $this->gen_password();
        $toUpdate['password'] = Crypt::encryptString($password);
        $updated = DB::collection(env('ACCOUNTS_DB'))->where('item_id', $id)->update($toUpdate, ['upsert' => false]);
        if ($updated) {
            $user_data = DB::collection(env('ACCOUNTS_DB'))->where('item_id', $id)->first();
            $user_data['password'] = $password;
            $this->send_email('password_reset_admin', $user_data);
            return response()->json('Contraseña generada satisfactoriamente, la contraseña a sido enviada al correo electrónico del usuario', 200);
        } else {
            return response()->json('Ocurrió un error al resetear la contraseña del usuario', 400);
        }
    }

    public function register(Request $data) {
        $body = $data->json()->all();
        try {
            $password = $this->gen_password();
            $item = $body['item'];
            $email = $item['email'];
            $attributes = ['item_id', 'timestamp'];
            $preview_user = DB::collection(env('ACCOUNTS_DB'))->where('email',$email)->get($attributes);
            if (sizeof($preview_user)>0) {
                return response()->json('El correo electrónico proporcionado ya se encuentra asociado a una cuenta', 400);
            }
            $item['timestamp'] = date('Y-m-d H:i:s');
            $item['item_id'] = uniqid();
            $item['disabled'] = false;
            $item['active'] = true;
            $item['login_tries'] = 0;
            $item['password'] = Crypt::encryptString($password);
            DB::collection(env('ACCOUNTS_DB'))->insert($item);
            $item['password'] = $password;
            $this->send_email('register', $item);
            return response()->json('Cuenta creada satisfactoriamente, la contraseña a sido enviada al correo electrónico proporcionado', 200);
        } catch( Exception $e ) {
            return response()->json('Error al crear la cuenta, debe proporcionar un objeto item con el email al que se asociará la cuenta', 400);
        }
    }

    public function upload_users(Request $data) {
        $toReturn = [];
        $body = $data->json()->all();
        foreach($body['items'] as $item){
            $item['item_id'] = uniqid();
            $item['timestamp'] = date('Y-m-d H:i:s');
            $item['disabled'] = false;
            $item['active'] = true;
            $item['login_tries'] = 0;
            $item['password'] = Crypt::encryptString($item['email']);
            DB::collection(env('ACCOUNTS_DB'))->insert($item);
            array_push($toReturn,$item);
        }
        return response()->json($toReturn, 200);
    }

    public function get_users(Request $data) {
        $id = $data['item_id'];
        $body = $data->json()->all();
        if (array_key_exists('output_model', $body)) {
            $output_model = $body['output_model'];
            $attributes = ['item_id', 'timestamp'];
            foreach($output_model as $key=>$value) {
                if ($value) {
                    array_push($attributes, $key);
                }
            }
        } else {
            $attributes = false;
        }
        if (array_key_exists('filter', $body)) {
            $filter = $body['filter'];
        } else {
            $filter = false;
        }
        $toReturn = DB::collection(env('ACCOUNTS_DB'));
        if ($filter) {
            $toReturn = $toReturn->where($filter['attribute'], $filter['value']);
        } else {
            if ($id) {
                $toReturn = $toReturn->where('item_id',$id);
            }
        }
        if ($attributes) {
            $toReturn = $toReturn->get($attributes);
        } else {
            $toReturn = $toReturn->get();
        }
        $users = [];
        foreach($toReturn as $user) {
            unset($user['password']);
            array_push($users, $user);
        }
        return response()->json($users, 200);
    }

    public function update_user(Request $data) {
        $body = $data->json()->all();
        $id = $body['item_id'];
        $item = $body['item'];
        $item['timestamp'] = date('Y-m-d H:i:s');
        $item['password'] = Crypt::encryptString($item['password']);
        $updated = DB::collection(env('ACCOUNTS_DB'))->where('item_id', $id)->update($item, ['upsert' => false]);
        if ($updated) {
            return response()->json('Datos del Usuario Actualizados Correctamente', 200);
        } else {
            return response()->json('Ocurrió un error al intentar actualizar el usuario', 400);
        }
    }

    public function delete_user(Request $data) {
        $id = $data['item_id'];
        $deleted = DB::collection(env('ACCOUNTS_DB'))->where('item_id',$id)->delete();
        if ($deleted) {
            return response()->json('Usuario Eliminado Correctamente', 200);
        } else {
            return response()->json('Ocurrió un error al intentar eliminar el usuario', 400);
        }
    }

    public function lock_user(Request $data) {
        $id = $data['item_id'];
        $toUpdate = [];
        $toUpdate['timestamp'] = date('Y-m-d H:i:s');
        $toUpdate['disabled'] = true;
        $updated = DB::collection(env('ACCOUNTS_DB'))->where('item_id', $id)->update($toUpdate, ['upsert' => false]);
        if ($updated) {
            return response()->json('Usuario Bloqueado Correctamente', 200);
        } else {
            return response()->json('Ocurrió un error al intentar bloquear el usuario', 400);
        }
    }

    public function unlock_user(Request $data) {
        $id = $data['item_id'];
        $toUpdate = [];
        $toUpdate['timestamp'] = date('Y-m-d H:i:s');
        $toUpdate['disabled'] = false;
        $updated = DB::collection(env('ACCOUNTS_DB'))->where('item_id', $id)->update($toUpdate, ['upsert' => false]);
        if ($updated) {
            return response()->json('Usuario Desbloqueado Correctamente', 200);
        } else {
            return response()->json('Ocurrió un error al intentar desbloquear el usuario', 400);
        }
    }

    private function send_email($tipo, $userdata) {
        $toAlias = $userdata['email'];
        $to = $userdata['email'];
        $fromMail = env('MAIL_FROM_ADDRESS');
        $fromAlias = env('APP_NAME');
        $body = '';
        $subject = '';
        $blade_mail = 'mail';
        switch($tipo) {
            case 'password_reset_admin':
                $subject = 'Reseteo de Contraseña';
                $blade_mail = 'password_reset';
                $data = ['name'=>$toAlias, 'password'=>$userdata['password'], 'appName'=>env('APP_NAME')];
                break;
            case 'password_recovery_request':
                $body = 'Para cambiar su contraseña de click en el siguiente enlace: ';
                $subject = 'Solicitud de Reseteo de Contraseña';
                $blade_mail = 'password_reset_request';
                $data = ['name'=>$toAlias, 'token'=>$userdata['recovery_token'], 'appName'=>env('APP_NAME'), 'url_reset_password_request'=>env('APP_URL')];
                break;
            case 'password_reset':
                $subject = 'Reseteo de Contraseña';
                $blade_mail = 'password_reset';
                $data = ['name'=>$toAlias, 'password'=>$userdata['password'], 'appName'=>env('APP_NAME')];
                break;
            case 'register':
                $body = 'Su contraseña es: ' . $userdata['password'];
                $subject = 'Creación de Cuenta';
                $blade_mail = 'mail';
                $data = ['name'=>$toAlias, 'body'=>$body, 'appName'=>env('APP_NAME')];
                break;
        }
        Mail::send($blade_mail, $data, function($message) use ($to, $toAlias, $subject, $fromMail,$fromAlias) {
          $message->to($to, $toAlias)->subject($subject);
          $message->from($fromMail,$fromAlias);
        });
    }

    private function gen_password() {
        return Str::random(env('PASWORD_LENGTH'));
    }

    private function gen_token($email, $token_lifetime) {
        $token = [
            'email' => $email,
            'expiration_time' => time() + $token_lifetime * 60
        ];
        return JWT::encode($token, env('JWT_SECRET'));
    }
}
