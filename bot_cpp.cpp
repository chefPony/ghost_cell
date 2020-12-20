#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <math.h>
#include <array>
#include <list>
#include <map>
#include <chrono>

int FORWARD = 4;
float PENALTY = 0.9;

using namespace std;

const map<int, int> PLAYER_MAP = {{1, 0}, {-1, 1}};

int sign(int x){
    return (x > 0) - (x < 0);
};

struct Factory{
    int entity_id, player, troops, prod, damage, arrivedTroops = 0;
    string entity_type = "FACTORY";
};

struct Troop{
    int entity_id, player,  source, destination, troops, distance;
    string entity_type = "TROOP";
};

struct Bomb{
    int entity_id, player, source, destination, distance;
    string entity_type = "BOMB";
};

class GameState{
    public:
        int bomb_reserve[2] = {2 , 2};
        int factoryCount, linkCount;
        vector<vector<int> > distanceMatr;
        vector<Factory > factories;
        list<Troop > troops;
        list<Bomb > bombs;
        GameState (int , int);
        void addLink(int factory1, int factory2, int distance){
            this->distanceMatr[factory1][factory2] = distance;
            this->distanceMatr[factory2][factory1] = distance;
        };
        void addFactory(int entity_id,  int player, int troops, int prod, int damage, int arg_6){
            this->factories[entity_id] = {entity_id, player, troops, prod, damage};
        }; 
        void addTroop(int entity_id, int player, int source, int destination, int troops, int distance){
            this->troops.push_back({entity_id, player, source, destination, troops, distance});
        };
        void addBomb(int entity_id,  int player, int source, int destination, int distance, int arg_6){
            this->bombs.push_back({entity_id, player, source, destination, distance});
        };
        void addEntity(int entity_id, string entity_type, int arg_1, int arg_2, int arg_3, int arg_4, int arg_5){
            if (entity_type == "FACTORY") 
                this->addFactory(entity_id, arg_1, arg_2, arg_3, arg_4, arg_5);
            if (entity_type == "TROOP") 
                this->addTroop(entity_id, arg_1, arg_2, arg_3, arg_4, arg_5);
            if (entity_type == "BOMB") 
                this->addBomb(entity_id, arg_1, arg_2, arg_3, arg_4, arg_5);
        };
        void clearMovingEntities(){
            this->troops.clear();
            this->bombs.clear();
        };
        void  moveEntities(){
            list<Troop > :: iterator troop;
            list<Bomb > :: iterator bomb;
            for(troop=this->troops.begin(); troop!=this->troops.end(); ++troop){
                troop->distance -= 1;
            };
            for(bomb=this->bombs.begin(); bomb!=this->bombs.end(); ++bomb){
                bomb->distance -= 1;
            };
        };
        void produce(){
            vector<Factory > :: iterator factory;
            for(factory=this->factories.begin(); factory!=this->factories.end(); ++factory){
                factory->troops += factory->prod * (factory->damage == 0) * (factory->player != 0);
                factory->damage -= 1 * (factory->damage > 0);
            };
        };
        void solveBattles();
        void nextState();
        float score(int player);
};

GameState :: GameState(int arg1, int arg2){
    this->factoryCount = arg1;
    this->linkCount = arg2;
    this->factories.resize(factoryCount);
    this->distanceMatr.resize(factoryCount);
    for (int i = 0; i<factoryCount; i++){
        this->distanceMatr[i].resize(factoryCount, 0);
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

float GameState :: score(int player){
    vector<Factory > :: iterator factory;
    list<Troop > :: iterator troop;
    float points = 0;
    for(factory= this->factories.begin(); factory != this->factories.end(); ++factory){
        if (factory->player == player)
            points += factory->troops + factory->prod * 10 + 5;
    };
    for(troop= this->troops.begin(); troop != this->troops.end(); ++troop){
        if (troop->player == player)
            points += troop->troops * pow(0.9, troop->distance);
    };
    return points;
};

class Action{
    protected:
        string prefix;
    public:
        Action(string prefix){
            this->prefix = prefix;
        };
        virtual string toStr(){return prefix;};
        virtual bool is_valid(const GameState &S, const int player) {return true;};
        virtual void apply(GameState &S, const int player){};
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
            string moveStr = {this->prefix + " " + to_string(this->source) + " " + to_string(this->target) + " " + to_string(this->troops)};
            return moveStr;
        };
        bool is_valid(const GameState &S, const int player) {
            if (S.factories[this->source].player == player && this->source != this->target && this->troops > 0){
                return true;
            }
            else{
                return false;
            };
        };
        void apply(GameState& S, const int player){
            S.factories[this->source].troops -= this->troops;
            S.addTroop(-1, player, this->source, this->target, this->troops, S.distanceMatr[this->source][this->target]);
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
            string bombStr = {this->prefix + " " + to_string(this->source) + " " + to_string(this->target)};
            return bombStr;
        };
        bool is_valid(const GameState &S, const int player){
            //cerr <<"FUUUUUUU" << S.bomb_reserve[PLAYER_MAP.at(player)] << endl;
            if (S.factories[this->source].player == player && this->source != this->target && S.bomb_reserve[PLAYER_MAP.at(player)] > 0){
                return true;
            }
            else{
                return false;
            }
        };
        void apply(GameState& S, const int player){
            S.addBomb(-1, player, this->source, this->target, S.distanceMatr[this->source][this->target], 0);
            S.bomb_reserve[PLAYER_MAP.at(player)] -= 1;
        };
};

class IncProd: public Action{
    int factory;
    public:
        IncProd(int factory):
            Action("INC")
        {
            this->factory = factory;
        };
        string toStr(){
            string incStr = {this->prefix + " " + to_string(this->factory)};
            return incStr;
        };
        bool is_valid(const GameState &S, const int player){
            if (S.factories[this->factory].player == player && S.factories[this->factory].troops >= 10 && S.factories[this->factory].prod < 3){
                return true;
            }
            else{
                return false;
            }
        };
        void apply(GameState& S, const int player){
            S.factories[this->factory].prod += 1;
            S.factories[this->factory].troops -= 10;
        };
};

class Player{
    int player_id;
    int n_bombs = 2; 
    public:
        Player(int player_id){this->player_id = player_id;};
        list<Action* > available_actions(GameState& S){
            list<Action* > action_superset;
            vector<Factory > :: iterator factory_1, factory_2;
            for (factory_1=S.factories.begin(); factory_1!=S.factories.end(); ++factory_1){
                if (factory_1->player == player_id){
                     action_superset.push_back(new IncProd(factory_1->entity_id));
                    for (factory_2=S.factories.begin(); factory_2!=S.factories.end(); ++factory_2){
                        if (factory_1 != factory_2 && factory_2->player == -this->player_id)
                            action_superset.push_back(new SendBomb(factory_1->entity_id, factory_2->entity_id));
                        if (factory_1 != factory_2)
                            action_superset.push_back(new SendTroops(factory_1->entity_id, factory_2->entity_id, (int) factory_1->troops*0.3));
                    };
                };
            };
            return action_superset;
        };
        float evaluate(Action* action, GameState S, int forward, float penalty){
            int step = 0;
            float action_score;
            float initial_score = S.score(this->player_id);
            action->apply(S, this->player_id);
            //cerr << "In evaluate Action.." << action->toStr() << endl;
            S.produce();
            S.solveBattles();
            action_score = S.score(this->player_id) - initial_score;
            for (step = 1; step < forward; ++step){
                S.moveEntities();
                S.produce();
                S.solveBattles();
                action_score += (S.score(this->player_id) - initial_score) * penalty;
                penalty *= penalty;
            };
            return action_score;
        };
        list <Action* > find_best_plan(GameState& S, int forward, float penalty){
            list <Action* > action_plan, action_superset = available_actions(S);
            Action* wait_action = new Action("WAIT");
            Action* best_action = new Action("WAIT");
            float wait_value = this->evaluate(wait_action, S, forward, penalty);
            bool is_first = true;
            auto start = chrono::system_clock::now();
            auto end = chrono::system_clock::now();
            cerr << "Wait value.." << wait_value << endl;
            chrono::duration<double> elapsed_seconds = end-start;
            while (is_first || best_action->toStr()!="WAIT" && elapsed_seconds.count()<0.04){
                float best_value = wait_value;
                best_action = wait_action;
                list <Action* > :: iterator current_action;
                for (current_action=action_superset.begin(); current_action!=action_superset.end(); ++current_action){
                    float a_value = wait_value;
                    //cerr << "Action.." << (*current_action)->toStr() << endl;
                    //cerr << "Valid.." << (*current_action)->is_valid(S, this->player_id) << endl;
                    if ((*current_action)->is_valid(S, player_id)){
                        a_value = this->evaluate(*current_action, S, forward, penalty);
                        cerr << "Action.." << (*current_action)->toStr() << endl;
                        cerr << "Value..."<< a_value << endl;
                    }
                    else 
                        current_action = action_superset.erase(current_action);
                    if (a_value > best_value){
                        best_value = a_value;
                        best_action = *current_action;
                    };  
                    end = chrono::system_clock::now();
                    elapsed_seconds = end-start;
                    if (elapsed_seconds.count() > 0.04){
                        break;
                    }
                }
                action_plan.push_back(best_action);
                /*cerr << "BEFORE APPLY" << endl;
                cerr << "Bombs Remaining.."<< S.bomb_reserve[PLAYER_MAP.at(this->player_id)] << endl;
                cerr << "Troops Moving.."<< S.troops.size() << endl;
                cerr << "Bomb Moving.."<< S.bombs.size() << endl;*/
                best_action->apply(S, this->player_id);
                /*cerr << "APPLY" << endl;
                cerr << "Best Action.." << best_action->toStr() << endl;
                cerr << "Value..."<< best_value << endl;
                cerr << "AFTER APPLY" << endl;
                cerr << "Bombs Remaining.."<< S.bomb_reserve[PLAYER_MAP.at(this->player_id)] << endl;
                cerr << "Troops Moving.."<< S.troops.size() << endl;
                cerr << "Bomb Moving.."<< S.bombs.size() << endl;*/
                is_first = false;
            };
            return action_plan;
        };
};


/**
 * Auto-generated code below aims at helping you parse
 * the standard input according to the problem statement.
 **/

int main()
{   
    Player player = Player(1);
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
        list<Action* > plan = player.find_best_plan(state, 6, 0.9);
        list<Action* > :: iterator current_action;
        string command = "";
        for (current_action=plan.begin(); current_action!=plan.end(); ++current_action)
            command += (*current_action)->toStr() + ";";
        // Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
        //cout << "WAIT" << endl;
        //cout << wait.toStr() << endl;
        cout << command.substr(0, command.size()-1) << endl;
    }
}