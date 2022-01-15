<?php

namespace App\Http\Controllers;

use App\Models\DummyModel;
use Illuminate\Http\Request;
use Exception;
use App\Http\Controllers\Controller;
use Illuminate\Support\Facades\Config;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Illuminate\Support\Facades\DB;
use stdClass;

class CatalogController extends Controller {

    public function upload_items(Request $data, $folder) {
        $toReturn = [];
        $body = $data->json()->all();
        foreach($body['items'] as $item){
            $item['item_id'] = uniqid();
            $item['timestamp'] = date('Y-m-d H:i:s');
            DB::collection($folder)->insert($item);
            array_push($toReturn,$item);
        }
        return response()->json($toReturn, 200);
    }

    public function get_items(Request $data, $folder, $dbname) {
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
        $toReturn = DB::collection($folder);
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
        return response()->json($toReturn, 200);
    }

    public function update_item(Request $data, $folder) {
        $body = $data->json()->all();
        $id = $body['item_id'];
        $item = $body['item'];
        $item['timestamp'] = date('Y-m-d H:i:s');
        $updated = DB::collection($folder)->where('item_id', $id)->update($item, ['upsert' => false]);
        if ($updated) {
            return response()->json('Datos Actualizados Correctamente', 200);
        } else {
            return response()->json('Ocurrió un error al intentar actualizar el item', 400);
        }
    }

    public function delete_item(Request $data, $folder) {
        $id = $data['item_id'];
        $deleted = DB::collection($folder)->where('item_id',$id)->delete();
        if ($deleted) {
            return response()->json('Item Eliminado Correctamente', 200);
        } else {
            return response()->json('Ocurrió un error al intentar eliminar el item', 400);
        }
    }

}
