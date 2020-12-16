#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <math.h>
#include <array>
#include <list>
#include <map>
using namespace std;

const int ID = 0; 
const int PLAYER = 1; 
const int TROOPS = 2;
const int PROD = 3;
const int FROM = 2; 
const int TO = 3;
const int SIZE = 4;
const int DIST = 5;
const int BLOCKED = 5;

int sign(int x){
    return (x > 0) - (x < 0);
};

struct Factory{
    int entity_id, player, troops, prod, damage, arrivedTroops = 0;
    string entity_type = "FACTORY";
};

struct Troop{
    int entity_id, player, troops, source, destination, distance;
    string entity_type = "TROOP";
};

struct Bomb{
    int entity_id, player, source, destination, distance;
    string entity_type = "BOMB";
};

class GameState{
    public:
        int factoryCount, linkCount;
        vector<vector<int> > distanceMatr;
        vector<Factory > factories;
        list<Troop > troops;
        list<Bomb > bombs;
        GameState (int , int);
        void addLink(int factory1, int factory2, int distance);
        void addFactory(int , int , int , int , int, int);
        void addTroop(int , int , int , int , int, int);
        void addBomb(int , int , int , int , int, int);
        void addEntity(int, string, int, int, int ,int, int);
        void clearMovingEntities();
        void moveEntities();
        void produce();
        void solveBattles();
        void nextState();
};

GameState :: GameState(int arg1, int arg2){
    this->factoryCount = arg1;
    this->linkCount = arg2;
    this->factories.resize(factoryCount);
    this->distanceMatr.resize(factoryCount);
    for (int i = 0; i<factoryCount; i++){
        this->distanceMatr[i].resize(factoryCount, 0);
    }
};

void GameState :: addLink(int factory1, int factory2, int distance){
    this->distanceMatr[factory1][factory2] = distance;
    this->distanceMatr[factory2][factory1] = distance;
};

void GameState :: addFactory(int entity_id,  int player, int troops, int prod, int damage, int arg_6){
    this->factories[entity_id] = {entity_id, player, troops, prod, damage};
}; 

void GameState :: addTroop(int entity_id, int player, int source, int destination, int troops, int distance){
    this->troops.push_back({entity_id, player, source, destination, troops, distance});
};

void GameState :: addBomb(int entity_id,  int player, int source, int destination, int distance, int arg_6){
    this->bombs.push_back({entity_id, player, source, destination, distance});
};

void GameState :: addEntity(int entity_id, string entity_type, int arg_1, int arg_2, int arg_3, int arg_4, int arg_5){
    if (entity_type == "FACTORY") 
        this->addFactory(entity_id, arg_1, arg_2, arg_3, arg_4, arg_5);
    if (entity_type == "TROOP") 
        this->addTroop(entity_id, arg_1, arg_2, arg_3, arg_4, arg_5);
    if (entity_type == "BOMB") 
        this->addBomb(entity_id, arg_1, arg_2, arg_3, arg_4, arg_5);
};

void GameState :: clearMovingEntities(){
    this->troops.clear();
    this->bombs.clear();
};

void GameState :: moveEntities(){
    list<Troop > :: iterator troop;
    list<Bomb > :: iterator bomb;
    for(troop=this->troops.begin(); troop!=this->troops.end(); ++troop){
        troop->distance -= 1;
    };
    for(bomb=this->bombs.begin(); bomb!=this->bombs.end(); ++bomb){
        bomb->distance -= 1;
    };
};

void GameState :: produce(){
    vector<Factory > :: iterator factory;
    for(factory=this->factories.begin(); factory!=this->factories.end(); ++factory){
        factory->troops += factory->prod * (factory->damage == 0);
    };
};

void GameState :: solveBattles(){
    list<Troop > :: iterator troop;
    for(troop=this->troops.begin(); troop!=this->troops.end(); ++troop){
        if (troop->distance == 0){
            int target = troop->destination;
            this->factories[target].arrivedTroops += troop->troops * troop->player;
            troop = this->troops.erase(troop);
        }
    };
    vector<Factory > :: iterator factory;
    for (factory=this->factories.begin(); factory!=this->factories.end(); ++factory){
        if (factory->player != sign(factory->arrivedTroops)){
            factory->player = (factory->troops >= factory->arrivedTroops) ? factory->player : sign(factory->arrivedTroops);
            factory->troops = abs(factory->troops - abs(factory->arrivedTroops));
        }
        else
        {
            factory->troops += abs(factory->arrivedTroops);
        };
        factory->arrivedTroops = 0;
    };
    list<Bomb > :: iterator bomb;
    for(bomb=this->bombs.begin(); bomb!=this->bombs.end(); ++bomb){
        if (bomb->distance == 0 and bomb->destination!=-1){
            int target = bomb->destination;
            int destroy = floor(this->factories[target].troops / 2);
            destroy = max(destroy, 10);
            if(destroy > this->factories[target].troops)
                this->factories[target].troops = 0;
            else
            {
                this->factories[target].troops -= destroy;
            }
            this->factories[target].damage = 5;
            bomb = this->bombs.erase(bomb);
        }
    };
};

class Action{
    protected:
        string prefix;
    public:
        Action(string prefix){
            this->prefix = prefix;
        };
        string toStr(){
            return prefix;
        };
};

class SendTroops: public Action{
    int source, target, troops;
    public:
        SendTroops(int source, int target, unsigned int troops):
            Action("MOVE")
        {
            this->source = source;
            this->target = target;
            this->troops = troops;
        };
        string toStr(){
            string moveStr = {this->prefix + " " + (char)this->source + " " + (char)this->target + " " + (char)this->troops};
            return moveStr;
        };
};

class SendBomb: public Action{
    int source, target;
    public:
        SendBomb(int source, int target):
            Action("BOMB")
        {
            this->source = source;
            this->target = target;
        };
        string toStr(){
            string bombStr = {this->prefix + " " + (char)this->source + " " + (char)this->target};
            return bombStr;
        };
};


/*void apply_action(GameState &S, Action action){
    if (action.prefix == "MOVE"){

    }
}*/
/**
 * Auto-generated code below aims at helping you parse
 * the standard input according to the problem statement.
 **/

int main()
{   

    int factoryCount; // the number of factories
    cin >> factoryCount; cin.ignore();
    int linkCount; // the number of links between factories
    cin >> linkCount; cin.ignore();
    GameState state(factoryCount, linkCount);
    for (int i = 0; i < linkCount; i++) {
        int factory1;
        int factory2;
        int distance;
        cin >> factory1 >> factory2 >> distance; cin.ignore();
        state.addLink(factory1, factory2, distance);
    }
    cerr << "Factories..."<< state.factoryCount << endl;
    cerr << "Link..."<< state.distanceMatr[0][1] << endl;
    // game loop
    while (1) {
        int entityCount; // the number of entities (e.g. factories and troops)
        cin >> entityCount; cin.ignore();
        state.clearMovingEntities();
        for (int i = 0; i < entityCount; i++) {
            int entityId;
            string entityType;
            int arg1;
            int arg2;
            int arg3;
            int arg4;
            int arg5;
            cin >> entityId >> entityType >> arg1 >> arg2 >> arg3 >> arg4 >> arg5; cin.ignore();
            state.addEntity(entityId, entityType, arg1, arg2, arg3, arg4, arg5);
        }
        cerr << "Factories..."<< state.factories.size() << endl;
        cerr << "Troops..."<< state.troops.size() << endl;
        cerr << "Bombs..."<< state.bombs.size() << endl;
        // Write an action using cout. DON'T FORGET THE "<< endl"
        // To debug: cerr << "Debug messages..." << endl;

        Action wait = Action("WAIT");
        // Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
        //cout << "WAIT" << endl;
        cout << wait.toStr() << endl;
    }
}