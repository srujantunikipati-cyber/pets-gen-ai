import { ObjectType, Field } from "type-graphql";

@ObjectType()
export class PetRoastData {
    @Field()
    jobId!: string;

    @Field()
    status!: string;
}

@ObjectType()
export class PetRoastResponse {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => PetRoastData, { nullable: true })
    data?: PetRoastData;
}
