import { GraphQLScalarType } from "graphql";

export const GraphQLUpload = new GraphQLScalarType({
    name: "Upload",
    description: "The `Upload` scalar type represents a file upload.",
});

export type FileUpload = {
    createReadStream: () => NodeJS.ReadableStream;
    filename: string;
    mimetype: string;
    encoding: string;
};
