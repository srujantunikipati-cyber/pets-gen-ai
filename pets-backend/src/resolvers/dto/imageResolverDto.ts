import { ObjectType, Field } from "type-graphql";

@ObjectType()
export class ImageGenerationData {
    @Field({ nullable: true })
    image?: string; // Base64 encoded image

    @Field({ nullable: true })
    jobId?: string;

    @Field({ nullable: true })
    status?: string;

    @Field({ nullable: true })
    videoUrl?: string;

    @Field({ nullable: true })
    inputImageUrl?: string;
}

@ObjectType()
export class ImageGenerationResponse {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => ImageGenerationData, { nullable: true })
    data?: ImageGenerationData;
}
