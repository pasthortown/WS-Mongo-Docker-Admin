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
    return 'Andres Romero';
});

$router->group(['prefix'=>'/{dbname}/{folder}','middleware'=>['multidb']], function() use ($router) {
    $router->post('get_items', ['uses'=>'CatalogController@get_items']);
    $router->post('upload_items', ['uses'=>'CatalogController@upload_items']);
    $router->put('update_item', ['uses'=>'CatalogController@update_item']);
    $router->get('search_items', ['uses'=>'CatalogController@search_items']);
    $router->delete('delete_item', ['uses'=>'CatalogController@delete_item']);
});



