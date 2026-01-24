class User{
    name: string;
    age: number;
    constructor(name: string, age: number){
        this.name = name;
        this.age = age;
    }
}

const user = new User("alice", 18);

console.log("user name: %d", user.age)