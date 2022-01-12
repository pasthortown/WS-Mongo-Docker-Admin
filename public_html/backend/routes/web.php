<?php

/** @var \Laravel\Lumen\Routing\Router $router */

/*
|--------------------------------------------------------------------------
| Application Routes
|--------------------------------------------------------------------------
|
| Here is where you can register all of the routes for an application.
| It is a breeze. Simply tell Lumen the URIs it should respond to
| and give it the Closure to call when that URI is requested.
|
*/

$router->get('/', function () use ($router) {
    return 'WS MONGO BDD';
});

$router->get('/key', function() {
    return \Illuminate\Support\Str::random(32);
});

$router->group(['prefix'=>'/{dbname}/{folder}', 'middleware'=>['multidb', 'auth']], function() use ($router) {
    $router->post('get_items', ['uses'=>'CatalogController@get_items']);
    $router->post('upload_items', ['uses'=>'CatalogController@upload_items']);
    $router->put('update_item', ['uses'=>'CatalogController@update_item']);
    $router->delete('delete_item', ['uses'=>'CatalogController@delete_item']);
});

$router->group(['prefix'=>'/{folder}', 'middleware'=>['multidmz']], function() use ($router) {
    $router->post('get_items', ['uses'=>'CatalogController@get_items']);
    $router->post('upload_items', ['uses'=>'CatalogController@upload_items']);
    $router->put('update_item', ['uses'=>'CatalogController@update_item']);
    $router->delete('delete_item', ['uses'=>'CatalogController@delete_item']);
});

$router->group(['prefix'=>'/api/auth/user', 'middleware'=>['bddauth']], function() use ($router) {
    $router->post('login', ['uses'=>'AuthController@login']);
    $router->post('register', ['uses'=>'AuthController@register']);
    $router->get('recovery', ['uses'=>'AuthController@recovery']);
    $router->get('reset_password', ['uses'=>'AuthController@reset_password']);
});

$router->group(['prefix'=>'/api/auth/user', 'middleware'=>['auth']], function() use ($router) {
    $router->post('upload_users', ['uses'=>'AuthController@upload_users']);
    $router->post('get_users', ['uses'=>'AuthController@get_users']);
    $router->put('update_user', ['uses'=>'AuthController@update_user']);
    $router->delete('delete_user', ['uses'=>'AuthController@delete_user']);
    $router->get('lock_user', ['uses'=>'AuthController@lock_user']);
    $router->get('unlock_user', ['uses'=>'AuthController@unlock_user']);
    $router->get('reset_password_user', ['uses'=>'AuthController@reset_password_user']);
});
